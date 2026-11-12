#!/usr/bin/env node
/*
 * Static analyzer for Vue 3 single-file components. It is read-only and never
 * writes to the project.
 *
 *   node analyze-vue.mjs <src-dir> [--json] [--min-dup-nodes=6]
 *
 * It parses with the target project's own @vue/compiler-sfc (resolved from the
 * nearest node_modules), so it needs no install of its own.
 *
 * It reports EVIDENCE, not verdicts. Every finding is a lead to verify by
 * reading the code. Categories:
 *   size        per-file line counts, API style, reactive primitive counts
 *   template    v-for key problems, v-if+v-for, derived lists computed in the
 *               template, per-row calls to iterating functions, repeated
 *               identical calls, logging during render, unresolved components
 *   script      deep watchers, listeners/timers without cleanup, deep clones,
 *               ref() payloads that could be shallowRef (only if never mutated
 *               in place), composables called inside helpers
 *   reuse       duplicate function bodies, divergent same-name helpers, helpers
 *               redefined despite a shared module, repeated template subtrees,
 *               watchers repeated across files, CSS grouped into style families
 *   structure   eager route imports, unused components, unrouted views
 */
import fs from 'node:fs'
import path from 'node:path'
import crypto from 'node:crypto'
import { createRequire } from 'node:module'

// ---------------------------------------------------------------- arguments
const args = process.argv.slice(2)
const srcDir = path.resolve(args.find((a) => !a.startsWith('--')) ?? 'src')
const asJson = args.includes('--json')
const minDupNodes = Number(args.find((a) => a.startsWith('--min-dup-nodes='))?.split('=')[1] ?? 6)

if (!fs.existsSync(srcDir)) {
  console.error(`Source directory not found: ${srcDir}`)
  process.exit(1)
}

// Resolve the compiler from the project being analyzed, walking up to node_modules
function resolveFromProject(id) {
  let dir = srcDir
  while (dir !== path.dirname(dir)) {
    try {
      return createRequire(path.join(dir, 'noop.js'))(id)
    } catch {
      dir = path.dirname(dir)
    }
  }
  console.error(`Could not resolve ${id} from ${srcDir}. Run from a Vue project with dependencies installed.`)
  process.exit(1)
}

const sfc = resolveFromProject('@vue/compiler-sfc')
const postcss = (() => {
  try {
    return resolveFromProject('postcss')
  } catch {
    return null
  }
})()

// ------------------------------------------------------------------ helpers
const rel = (file) => path.relative(process.cwd(), file)
const hash = (text) => crypto.createHash('sha1').update(text).digest('hex').slice(0, 12)
const normalizeCode = (code) =>
  code
    .replace(/\/\*[\s\S]*?\*\//g, '')
    .replace(/\/\/.*$/gm, '')
    .replace(/\s+/g, ' ')
    .trim()

function walkFiles(dir, out = []) {
  for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
    if (entry.name === 'node_modules' || entry.name.startsWith('.')) continue
    const full = path.join(dir, entry.name)
    if (entry.isDirectory()) walkFiles(full, out)
    else if (/\.(vue|js|ts|mjs)$/.test(entry.name)) out.push(full)
  }
  return out
}

// Template AST node types from @vue/compiler-core
const NODE = { ELEMENT: 1, TEXT: 2, COMMENT: 3, INTERPOLATION: 5, ATTRIBUTE: 6, DIRECTIVE: 7 }

const findings = []
const add = (category, rule, file, line, message, extra = {}) =>
  findings.push({ category, rule, file: rel(file), line, message, ...extra })

// --------------------------------------------------------- script analysis
// Returns the functions declared in a script plus per-file script findings
function analyzeScript(code, file, lineOffset, lang) {
  const functions = []
  const stats = { ref: 0, shallowRef: 0, reactive: 0, computed: 0, watch: 0, deepWatch: 0 }
  let ast
  try {
    ast = sfc.babelParse(code, {
      sourceType: 'module',
      plugins: lang === 'ts' ? ['typescript', 'jsx'] : ['jsx']
    })
  } catch (error) {
    add('script', 'parse-error', file, lineOffset + 1, `Script could not be parsed: ${error.message}`)
    return { functions, stats, refNames: new Set(), imports: new Set(), watchers: [], apiStyle: 'unknown' }
  }

  const line = (node) => lineOffset + node.loc.start.line
  const src = (node) => code.slice(node.start, node.end)
  const refNames = new Set()
  const imports = new Set()
  const watchers = []
  let apiStyle = 'none'

  // Enclosing-function stack, to tell setup-level code from code inside
  // helpers that may run per row
  const fnStack = []
  const isFn = (n) => ['FunctionDeclaration', 'FunctionExpression', 'ArrowFunctionExpression', 'ObjectMethod'].includes(n.type)
  const fnName = (n, parent) =>
    n.id?.name ?? n.key?.name ?? (parent?.type === 'VariableDeclarator' ? parent.id?.name : null) ??
    (parent?.type === 'ObjectProperty' ? parent.key?.name : null)

  sfc.walk(ast, {
    leave(node) {
      if (isFn(node)) fnStack.pop()
    },
    enter(node, parent) {
      if (isFn(node)) fnStack.push({ node, name: fnName(node, parent) })
      if (node.type === 'ImportDeclaration') {
        for (const s of node.specifiers) imports.add(s.local.name)
      }
      // API style detection
      if (node.type === 'ObjectProperty' || node.type === 'ObjectMethod') {
        const key = node.key?.name
        if (key === 'setup' && parent?.type === 'ObjectExpression') apiStyle = 'setup()'
        if ((key === 'data' || key === 'methods') && apiStyle === 'none') apiStyle = 'options'
      }

      // Named functions: const fn = () => {}, function fn() {}, and methods
      let name = null
      let fnNode = null
      if (node.type === 'FunctionDeclaration' && node.id) {
        name = node.id.name
        fnNode = node
      } else if (
        node.type === 'VariableDeclarator' &&
        node.id?.type === 'Identifier' &&
        ['ArrowFunctionExpression', 'FunctionExpression'].includes(node.init?.type)
      ) {
        name = node.id.name
        fnNode = node.init
      } else if (node.type === 'ObjectMethod' && node.key?.name && node.key.name !== 'setup') {
        name = node.key.name
        fnNode = node
      }
      if (name && fnNode?.body) {
        const body = src(fnNode.body)
        const normalized = normalizeCode(body)
        functions.push({
          name,
          file,
          line: line(fnNode),
          lines: fnNode.loc.end.line - fnNode.loc.start.line + 1,
          bodyHash: hash(normalized),
          size: normalized.length,
          // Does it iterate a collection? Calls to it once per v-for row multiply
          // cost. A for-loop counts only when bounded by reactive state
          // (this.items.length, items.value.length); loops over a local string
          // or number, as in formatters, are cheap.
          iterates:
            /\.(filter|map|reduce|forEach|find|findIndex|some|every|sort)\(|Math\.(max|min)\(\s*\.\.\./.test(body) ||
            /for\s*\([^;]*;[^;]*<\s*(this\.[\w.]+|\w+\.value[\w.]*)\.length/.test(body),
          logs: /\bconsole\.(log|debug|info|warn)\(/.test(body),
          // A thin wrapper that delegates to a same-named function elsewhere is
          // layering, not duplication: deleteTask -> api.deleteTask, or
          // formatCurrency -> an imported formatCurrencyUtil
          delegates:
            new RegExp(`\\.${name}\\s*\\(`).test(body) ||
            new RegExp(`\\b\\w*${name}\\w+\\s*\\(|\\b\\w+${name}\\w*\\s*\\(`, 'i').test(body)
        })
      }

      if (node.type !== 'CallExpression') return
      const callee = node.callee.type === 'Identifier' ? node.callee.name : node.callee.property?.name

      if (callee in stats) stats[callee]++

      // Composables belong at setup level. Called inside a helper, they re-run
      // (creating new refs and computeds) on every call, which may be per row.
      if (/^use[A-Z]/.test(callee ?? '') && node.callee.type === 'Identifier' && fnStack.length) {
        const inner = fnStack[fnStack.length - 1]
        const allowed = inner.name === 'setup' || /^use[A-Z]/.test(inner.name ?? '')
        if (!allowed) {
          add('script', 'composable-in-function', file, line(node),
            `${callee}() is called inside ${inner.name ?? 'a nested function'}(), so it runs again on every call (per row if the template calls it in v-for). Call it once at setup level and close over the result.`)
        }
      }

      if (callee === 'watch') {
        watchers.push({ file, line: line(node), hash: hash(normalizeCode(src(node))), sourceHash: hash(normalizeCode(src(node.arguments[0] ?? node))), source: normalizeCode(src(node.arguments[0] ?? node)).slice(0, 60) })
      }
      if ((callee === 'ref' || callee === 'shallowRef') && parent?.type === 'VariableDeclarator') {
        refNames.add(parent.id?.name)
      }

      if (callee === 'watch' || callee === 'watchEffect') {
        const options = node.arguments[2]
        const deep = options?.type === 'ObjectExpression' &&
          options.properties.some((p) => p.key?.name === 'deep' && p.value?.value === true)
        if (deep) {
          stats.deepWatch++
          add('script', 'deep-watch', file, line(node),
            'Deep watcher traverses the whole object on every change. Watch a getter for the specific fields, or the array length or ids.')
        }
      }

      if (callee === 'parse' && node.callee.object?.name === 'JSON' &&
          node.arguments[0]?.callee?.property?.name === 'stringify') {
        add('script', 'json-deep-clone', file, line(node),
          'JSON round-trip deep clone. Use structuredClone(), or avoid cloning if the data is read-only.')
      }
    }
  })

  // Listener and timer cleanup, checked per file on the raw text
  const pairs = [
    ['addEventListener', 'removeEventListener', 'listener-without-cleanup'],
    ['setInterval', 'clearInterval', 'interval-without-cleanup']
  ]
  for (const [setup, teardown, rule] of pairs) {
    const index = code.indexOf(`${setup}(`)
    if (index !== -1 && !code.includes(`${teardown}(`)) {
      const at = lineOffset + code.slice(0, index).split('\n').length
      add('script', rule, file, at,
        `${setup} with no ${teardown} in this file. It leaks when the component unmounts; clean up in onBeforeUnmount/onUnmounted.`)
    }
  }

  // Large API payloads stored in a deep ref(): candidates for shallowRef when
  // the data is replaced wholesale and never mutated in place
  const assignRe = /(\w+)\.value\s*=\s*await\s+[\w.]+\(/g
  for (const match of code.matchAll(assignRe)) {
    // In-place mutation (push, splice, index or field assignment) needs a deep
    // ref; shallowRef would silently stop updating the UI
    const mutated = new RegExp(
      `${match[1]}\\.value(\\.(push|unshift|splice|pop|shift|sort|reverse)\\(|\\[[^\\]]+\\]\\s*=[^=]|\\.\\w+\\s*=[^=])`
    ).test(code)
    if (refNames.has(match[1]) && !mutated) {
      const at = lineOffset + code.slice(0, match.index).split('\n').length
      add('script', 'ref-api-payload', file, at,
        `"${match[1]}" holds a whole API response in a deep ref(). If it is only ever replaced, never mutated per field, shallowRef() avoids deep proxying. Verify there are no in-place mutations first.`)
    }
  }

  return { functions, stats, refNames, imports, watchers, apiStyle }
}

// ------------------------------------------------------- template analysis
function parseVFor(content) {
  const m = content.match(/^\s*\(?\s*([^,()]+?)\s*(?:,\s*([^,()]+?))?\s*(?:,\s*([^()]+?))?\s*\)?\s+(?:in|of)\s+([\s\S]+)$/)
  if (!m) return null
  // With two aliases in an array loop the second is the index; with three
  // (object loop) the third is the index
  return { item: m[1], second: m[2], third: m[3], source: m[4].trim() }
}

const directive = (node, name, arg) =>
  node.props?.find((p) => p.type === NODE.DIRECTIVE && p.name === name && (!arg || p.arg?.content === arg))

const BUILTIN_TAGS = new Set([
  'router-link', 'router-view', 'transition', 'transition-group', 'keep-alive',
  'teleport', 'suspense', 'component', 'slot', 'template'
])
const pascal = (tag) => tag.replace(/(^|-)(\w)/g, (_, __, c) => c.toUpperCase())

function analyzeTemplate(ast, file, scriptFunctions, knownComponents) {
  const signatures = []
  const unresolved = new Set()
  const fnByName = new Map(scriptFunctions.map((f) => [f.name, f]))
  const iteratingFns = new Map(scriptFunctions.filter((f) => f.iterates).map((f) => [f.name, f]))
  // Every call expression in the template, to find repeated identical calls
  // and functions that log during render
  const templateCalls = []
  let nodeCount = 0
  let maxDepth = 0

  // Returns { sig, size } for structural duplicate detection
  function visit(node, depth, loopAliases) {
    if (node.type !== NODE.ELEMENT) return { sig: '', size: 0 }
    nodeCount++
    maxDepth = Math.max(maxDepth, depth)
    const line = node.loc.start.line

    // A PascalCase or hyphenated tag is a component. If it is neither imported,
    // globally registered, nor built in, Vue renders nothing and logs
    // "Failed to resolve component".
    const looksLikeComponent = /[A-Z]/.test(node.tag) || node.tag.includes('-')
    if (looksLikeComponent && !BUILTIN_TAGS.has(node.tag.toLowerCase().replace(/(?<=[a-z])(?=[A-Z])/g, '-'))) {
      const name = pascal(node.tag)
      if (!knownComponents.has(name) && !unresolved.has(name)) {
        unresolved.add(name)
        add('template', 'unresolved-component', file, line,
          `<${node.tag}> is used but not imported or globally registered. It renders nothing and Vue warns "Failed to resolve component". Import it, or remove it if it is unfinished.`)
      }
    }

    const vFor = directive(node, 'for')
    let aliases = loopAliases
    if (vFor) {
      const parsed = parseVFor(vFor.exp?.content ?? '')
      if (parsed) {
        const indexAlias = parsed.third ?? parsed.second
        aliases = [...loopAliases, parsed.item, parsed.second, parsed.third].filter(Boolean)
        const key = directive(node, 'bind', 'key')

        if (!key) {
          add('template', 'v-for-missing-key', file, line,
            `v-for="${vFor.exp.content}" has no :key. Vue patches by position, so state and DOM get reused for the wrong rows.`)
        } else if (indexAlias && key.exp?.content.trim() === indexAlias.trim()) {
          add('template', 'v-for-index-key', file, line,
            `:key="${key.exp.content}" uses the loop index. Reordering, filtering, or inserting rows remounts or mismatches them; key on a stable id.`)
        }

        if (directive(node, 'if')) {
          add('template', 'v-if-with-v-for', file, line,
            'v-if on the same element as v-for. In Vue 3, v-if runs first and cannot see the loop variable; filter in a computed instead.')
        }

        if (/\.(sort|reverse)\(/.test(parsed.source)) {
          add('template', 'mutating-sort-in-template', file, line,
            `v-for source "${parsed.source}" calls sort()/reverse(), which mutates reactive state during render (infinite-update risk). Sort a copy in a computed.`)
        } else if (/\(|\.(filter|map|slice)\(/.test(parsed.source)) {
          add('template', 'derived-list-in-template', file, line,
            `v-for source "${parsed.source}" is computed during render, so it re-runs on every re-render of this component. Move it to a computed() so it is cached.`)
        }
      }
    }

    // Render-time expressions on this node (event handlers excluded: they run on
    // interaction, not on render)
    const expressions = []
    for (const p of node.props ?? []) {
      if (p.type === NODE.DIRECTIVE && p.exp?.content && p.name !== 'on') expressions.push(p.exp.content)
    }
    for (const child of node.children ?? []) {
      if (child.type === NODE.INTERPOLATION) expressions.push(child.content?.content ?? '')
    }
    for (const expr of expressions) {
      // name(args) with balanced-enough args for one level of parentheses
      for (const m of expr.matchAll(/\b([A-Za-z_$][\w$]*)\s*\(([^()]*)\)/g)) {
        if (fnByName.has(m[1])) templateCalls.push({ name: m[1], text: `${m[1]}(${m[2].trim()})`, line })
      }
    }

    // Calls to iterating functions inside a loop: O(rows x n) work per render
    if (loopAliases.length) {
      for (const expr of expressions) {
        for (const m of expr.matchAll(/\b([A-Za-z_$][\w$]*)\s*\(/g)) {
          const fn = iteratingFns.get(m[1])
          if (fn) {
            add('template', 'iterating-call-per-row', file, line,
              `${m[1]}() iterates a collection (defined at line ${fn.line}) and is called for every v-for row: O(rows x n) per render. Hoist the iteration (max, lookup, filter) into a computed() and read the cached value per row.`)
          }
        }
      }
    }

    // Structural signature: tag, static classes, and child signatures (text ignored)
    const staticClass = node.props?.find((p) => p.type === NODE.ATTRIBUTE && p.name === 'class')?.value?.content ?? ''
    const children = (node.children ?? []).map((c) => visit(c, depth + 1, aliases)).filter((c) => c.sig)
    const sig = `${node.tag}.${staticClass.split(/\s+/).filter(Boolean).sort().join('.')}(${children.map((c) => c.sig).join(',')})`
    const size = 1 + children.reduce((sum, c) => sum + c.size, 0)
    if (size >= minDupNodes) {
      signatures.push({ hash: hash(sig), size, file, line, endLine: node.loc.end.line, tag: node.tag, staticClass })
    }
    return { sig, size }
  }

  for (const child of ast.children ?? []) visit(child, 1, [])

  // The same iterating call written several times re-runs the iteration each
  // time on every render; one computed() would run it once and cache it
  const byText = templateCalls.reduce((m, c) => m.set(c.text, [...(m.get(c.text) ?? []), c]), new Map())
  for (const [text, calls] of byText) {
    if (calls.length > 1 && iteratingFns.has(calls[0].name)) {
      add('template', 'repeated-call-in-template', file, calls[0].line,
        `${text} is evaluated ${calls.length} times per render (lines ${calls.map((c) => c.line).join(', ')}) and iterates each time. Cache it in one computed().`)
    }
  }

  // Logging inside functions the template calls runs on every render, per row
  const reported = new Set()
  for (const call of templateCalls) {
    const fn = fnByName.get(call.name)
    if (fn?.logs && !reported.has(fn.name)) {
      reported.add(fn.name)
      add('template', 'console-in-render', file, fn.line,
        `${fn.name}() logs to the console and is called from the template, so it logs on every render (and per row inside v-for). Remove the logging.`)
    }
  }

  return { signatures, nodeCount, maxDepth }
}

// ---------------------------------------------------------- style analysis
function analyzeStyles(styles, file) {
  const rules = []
  if (!postcss) return rules
  for (const style of styles) {
    if (style.lang && !['css', 'postcss'].includes(style.lang)) continue
    let root
    try {
      root = postcss.parse(style.content)
    } catch {
      continue
    }
    const offset = style.loc.start.line - 1
    root.walkRules((rule) => {
      if (rule.parent?.type === 'atrule' && /keyframes/.test(rule.parent.name)) return
      const decls = rule.nodes
        .filter((n) => n.type === 'decl')
        .map((d) => `${d.prop}:${d.value.replace(/\s+/g, ' ')}`)
        .sort()
      if (!decls.length) return
      rules.push({
        file,
        line: offset + (rule.source?.start?.line ?? 1),
        selector: rule.selector.replace(/\s+/g, ' '),
        declHash: hash(decls.join(';')),
        declCount: decls.length
      })
    })
  }
  return rules
}

// -------------------------------------------------------------------- main
const files = walkFiles(srcDir)
const vueFiles = files.filter((f) => f.endsWith('.vue'))
const jsFiles = files.filter((f) => !f.endsWith('.vue'))

const sizes = []
let allFunctions = []
let allSignatures = []
let allRules = []
let allWatchers = []

// Components registered globally with app.component('Name', ...)
const globalComponents = new Set()
for (const file of jsFiles) {
  for (const m of fs.readFileSync(file, 'utf8').matchAll(/\.component\(\s*['"]([\w-]+)['"]/g)) {
    globalComponents.add(pascal(m[1]))
  }
}

for (const file of vueFiles) {
  const source = fs.readFileSync(file, 'utf8')
  const { descriptor, errors } = sfc.parse(source, { filename: file })
  if (errors.length) add('size', 'sfc-parse-error', file, 1, errors[0].message)

  const script = descriptor.scriptSetup ?? descriptor.script
  let scriptResult = { functions: [], stats: {}, imports: new Set(), watchers: [], apiStyle: 'none' }
  if (script) {
    scriptResult = analyzeScript(script.content, file, script.loc.start.line - 1, script.lang)
    if (descriptor.scriptSetup) scriptResult.apiStyle = '<script setup>'
  }
  allFunctions = allFunctions.concat(scriptResult.functions)
  allWatchers = allWatchers.concat(scriptResult.watchers)

  let templateResult = { signatures: [], nodeCount: 0, maxDepth: 0 }
  if (descriptor.template?.ast) {
    const known = new Set([...globalComponents, ...scriptResult.imports])
    // A component can render itself recursively by its file name
    known.add(path.basename(file, '.vue'))
    templateResult = analyzeTemplate(descriptor.template.ast, file, scriptResult.functions, known)
  }
  allSignatures = allSignatures.concat(templateResult.signatures)
  allRules = allRules.concat(analyzeStyles(descriptor.styles, file))

  const blockLines = (block) => (block ? block.loc.end.line - block.loc.start.line + 1 : 0)
  sizes.push({
    file: rel(file),
    // Match `wc -l`: a trailing newline does not start another line
    total: source.split('\n').length - (source.endsWith('\n') ? 1 : 0),
    template: blockLines(descriptor.template),
    script: blockLines(script),
    style: descriptor.styles.reduce((sum, s) => sum + blockLines(s), 0),
    elements: templateResult.nodeCount,
    depth: templateResult.maxDepth,
    api: scriptResult.apiStyle,
    ...scriptResult.stats
  })
}

for (const file of jsFiles) {
  const code = fs.readFileSync(file, 'utf8')
  const result = analyzeScript(code, file, 0, file.endsWith('.ts') ? 'ts' : 'js')
  allFunctions = allFunctions.concat(result.functions)
}

// ---- reuse: identical function bodies in 2+ places
const byBody = Map.groupBy
  ? Map.groupBy(allFunctions.filter((f) => f.size >= 40), (f) => f.bodyHash)
  : allFunctions.filter((f) => f.size >= 40).reduce((m, f) => m.set(f.bodyHash, [...(m.get(f.bodyHash) ?? []), f]), new Map())
const duplicateBodies = [...byBody.values()].filter((group) => group.length > 1)

// ---- reuse: same helper name defined in 2+ files with different bodies
const byName = allFunctions
  .filter((f) => !f.delegates)
  .reduce((m, f) => m.set(f.name, [...(m.get(f.name) ?? []), f]), new Map())
const sameNameHelpers = [...byName.entries()]
  .filter(([name, group]) => new Set(group.map((f) => f.file)).size > 1 &&
    !/^(load\w*|fetch\w*|close|open|toggle|setup|handle\w*|on[A-Z]\w*|init)$/.test(name))
  .filter(([, group]) => new Set(group.map((f) => f.bodyHash)).size > 1)
  // Two unrelated functions can share a name (getBarHeight in two charts). Keep
  // a group when the name is recurring helper vocabulary, or when 3+ files
  // define it, which suggests divergent copies of one helper.
  .filter(([name, group]) =>
    /^(format|translate|parse|to[A-Z]|get\w*(Class|Status|Label|Color|Badge|Icon|Text))/.test(name) ||
    new Set(group.map((f) => f.file)).size >= 3)
  // A definition in a plain .js/.ts module means a shared helper already exists
  // and components are redefining it instead of importing it
  .map(([name, group]) => [name, group, group.some((f) => !f.file.endsWith('.vue'))])

// ---- reuse: repeated template subtrees, keeping only the largest overlapping matches
const bySig = allSignatures.reduce((m, s) => m.set(s.hash, [...(m.get(s.hash) ?? []), s]), new Map())
const covered = []
const duplicateTemplates = [...bySig.values()]
  .filter((group) => group.length > 1)
  .sort((a, b) => b[0].size - a[0].size)
  .filter((group) => {
    const inside = group.every((s) => covered.some((c) => c.file === s.file && s.line >= c.line && s.endLine <= c.endLine))
    if (!inside) covered.push(...group)
    return !inside
  })

// ---- reuse: identical CSS declaration blocks in 2+ files
const byDecls = allRules.filter((r) => r.declCount >= 3)
  .reduce((m, r) => m.set(r.declHash, [...(m.get(r.declHash) ?? []), r]), new Map())
// Small blocks (display:flex; gap; align-items) match by coincidence, so they
// only count when they recur in 3+ files
const duplicateCss = [...byDecls.values()].filter((g) => {
  const fileCount = new Set(g.map((r) => r.file)).size
  return fileCount >= 3 || (fileCount >= 2 && g[0].declCount >= 5)
})

// ---- reuse: the same selector restyled in 3+ files (shared component candidates)
const bySelector = allRules.reduce((m, r) => m.set(r.selector, [...(m.get(r.selector) ?? []), r]), new Map())
const repeatedSelectors = [...bySelector.entries()].filter(([, g]) => new Set(g.map((r) => r.file)).size >= 3)

// ---- reuse: the same watcher in several files (open/close sync, filter reloads)
const byWatchSource = allWatchers.reduce((m, w) => m.set(w.sourceHash, [...(m.get(w.sourceHash) ?? []), w]), new Map())
const repeatedWatchers = [...byWatchSource.values()]
  .filter((g) => new Set(g.map((w) => w.file)).size >= 3)
  .map((g) => ({ source: g[0].source, identical: new Set(g.map((w) => w.hash)).size === 1, at: g.map((w) => `${rel(w.file)}:${w.line}`) }))

// ---- reuse: style families. Selectors duplicated across the same set of
// files are one finding (e.g. six modals sharing overlay, header, and buttons),
// not dozens of separate entries.
const families = new Map()
const addToFamily = (filesInGroup, selector) => {
  const key = [...new Set(filesInGroup)].sort().join('|')
  if (!families.has(key)) families.set(key, { files: key.split('|'), selectors: new Set(), identical: 0 })
  families.get(key).selectors.add(selector)
  return families.get(key)
}
for (const group of duplicateCss) {
  for (const r of group) addToFamily(group.map((g) => rel(g.file)), r.selector).identical++
}
for (const [selector, group] of repeatedSelectors) addToFamily(group.map((r) => rel(r.file)), selector)
const styleFamilies = [...families.values()]
  .map((f) => ({ files: f.files, selectors: [...f.selectors], identicalBlocks: f.identical }))
  .sort((a, b) => b.selectors.length - a.selectors.length)

// ---- structure: route imports, unused components, unrouted views
const allSource = files.map((f) => [f, fs.readFileSync(f, 'utf8')])
for (const [file, code] of allSource) {
  if (!/createRouter\s*\(/.test(code)) continue
  for (const m of code.matchAll(/import\s+(\w+)\s+from\s+['"]([^'"]+\.vue)['"]/g)) {
    // Only imports used as a route component; the root App is not a route
    if (!new RegExp(`component\\s*:\\s*${m[1]}\\b`).test(code)) continue
    const at = code.slice(0, m.index).split('\n').length
    add('structure', 'eager-route-import', file, at,
      `${m[1]} (${m[2]}) is imported eagerly into the router, so it ships in the initial bundle. Use component: () => import('${m[2]}') for code splitting.`)
  }
}
for (const file of vueFiles) {
  const base = path.basename(file)
  const importers = allSource.filter(([f, code]) => f !== file && code.includes(base))
  if (!importers.length && !/App\.vue$/.test(file)) {
    const kind = /views?\//.test(file) ? 'unrouted-view' : 'unused-component'
    add('structure', kind, file, 1, `${base} is not imported anywhere. Confirm it is dead (or should be routed) before removing it.`)
  }
}

// -------------------------------------------------------------------- output
const report = {
  srcDir: rel(srcDir) || '.',
  sizes: sizes.sort((a, b) => b.total - a.total),
  findings,
  reuse: {
    duplicateBodies: duplicateBodies.map((g) => g.map(({ name, file, line, lines }) => ({ name, file: rel(file), line, lines }))),
    sameNameHelpers: sameNameHelpers.map(([name, g, sharedExists]) => ({ name, sharedHelperExists: sharedExists, defs: g.map((f) => ({ file: rel(f.file), line: f.line, lines: f.lines })) })),
    duplicateTemplates: duplicateTemplates.map((g) => ({ size: g[0].size, root: `<${g[0].tag}${g[0].staticClass ? ` class="${g[0].staticClass}"` : ''}>`, at: g.map((s) => `${rel(s.file)}:${s.line}`) })),
    repeatedWatchers,
    styleFamilies,
    duplicateCss: duplicateCss.map((g) => ({ decls: g[0].declCount, at: g.map((r) => `${rel(r.file)}:${r.line} ${r.selector}`) })),
    repeatedSelectors: repeatedSelectors.map(([selector, g]) => ({ selector, files: [...new Set(g.map((r) => rel(r.file)))] }))
  }
}

if (asJson) {
  console.log(JSON.stringify(report, null, 2))
  process.exit(0)
}

const out = []
out.push(`# Vue component analysis: ${report.srcDir}`, '')
out.push('## Size (largest first)', '')
out.push('| file | lines | tpl | script | style | elements | depth | api | ref | computed | watch |')
out.push('|---|---|---|---|---|---|---|---|---|---|---|')
for (const s of report.sizes) {
  out.push(`| ${s.file} | ${s.total} | ${s.template} | ${s.script} | ${s.style} | ${s.elements} | ${s.depth} | ${s.api} | ${s.ref ?? 0} | ${s.computed ?? 0} | ${s.watch ?? 0} |`)
}
for (const category of ['template', 'script', 'structure', 'size']) {
  const group = findings.filter((f) => f.category === category)
  if (!group.length) continue
  out.push('', `## ${category} findings (${group.length})`, '')
  for (const f of group) out.push(`- **${f.rule}** ${f.file}:${f.line}: ${f.message}`)
}
out.push('', '## Reuse', '')
out.push(`### Identical function bodies (${report.reuse.duplicateBodies.length})`)
for (const g of report.reuse.duplicateBodies) out.push(`- ${g.map((f) => `${f.name} @ ${f.file}:${f.line}`).join(' | ')}`)
out.push('', `### Same-name helpers with differing bodies (${report.reuse.sameNameHelpers.length})`)
for (const h of report.reuse.sameNameHelpers) {
  const note = h.sharedHelperExists ? ' (a shared module already defines it; components should import it)' : ''
  out.push(`- **${h.name}**${note}: ${h.defs.map((d) => `${d.file}:${d.line}`).join(', ')}`)
}
out.push('', `### Repeated template structures (${report.reuse.duplicateTemplates.length})`)
for (const t of report.reuse.duplicateTemplates) out.push(`- ${t.root} (${t.size} elements) at ${t.at.join(', ')}`)
out.push('', `### Watchers repeated in 3+ files (${report.reuse.repeatedWatchers.length})`)
for (const w of report.reuse.repeatedWatchers) {
  out.push(`- \`watch(${w.source}...)\`${w.identical ? ' (identical bodies)' : ''}: ${w.at.join(', ')}`)
}
out.push('', `### Style families: CSS shared across the same files (${report.reuse.styleFamilies.length})`)
out.push('Each family is one extraction candidate (a shared component or global class). Per-selector detail is in --json.')
for (const f of report.reuse.styleFamilies) {
  const shown = f.selectors.slice(0, 8).map((s) => `\`${s}\``).join(', ')
  const more = f.selectors.length > 8 ? ` +${f.selectors.length - 8} more` : ''
  out.push(`- **${f.files.length} files** (${f.files.map((x) => path.basename(x)).join(', ')}): ${f.selectors.length} selectors, ${f.identicalBlocks} byte-identical. ${shown}${more}`)
}
console.log(out.join('\n'))
