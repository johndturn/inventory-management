// Currency conversion utility
// USD to JPY exchange rate (approximate)
const USD_TO_JPY = 150

export function formatCurrency(amount, currency = 'USD') {
  if (currency === 'JPY') {
    const yenAmount = Math.round(amount * USD_TO_JPY)
    return `¥${yenAmount.toLocaleString('ja-JP')}`
  }
  // Default USD
  return `$${amount.toLocaleString('en-US', { maximumFractionDigits: 0 })}`
}

export function formatCurrencyWithDecimals(amount, currency = 'USD', decimals = 0) {
  if (currency === 'JPY') {
    const yenAmount = Math.round(amount * USD_TO_JPY)
    return `¥${yenAmount.toLocaleString('ja-JP')}`
  }
  // Default USD
  return `$${amount.toLocaleString('en-US', { minimumFractionDigits: decimals, maximumFractionDigits: decimals })}`
}

// Short form for chart axes and tight labels: $5.2M / ¥7.9億. Amounts are always
// stored in USD and converted here, so callers never prefix a symbol themselves
// (prefixing '¥' to a raw USD number shows a value 150x too small).
export function formatCurrencyCompact(amount, currency = 'USD') {
  const isJPY = currency === 'JPY'
  return new Intl.NumberFormat(isJPY ? 'ja-JP' : 'en-US', {
    style: 'currency',
    currency: isJPY ? 'JPY' : 'USD',
    notation: 'compact',
    maximumFractionDigits: 1
  }).format(isJPY ? amount * USD_TO_JPY : amount)
    // ja-JP Intl uses the full-width ￥; the rest of the app uses ¥
    .replace('￥', '¥')
}

export function convertAmount(amount, currency = 'USD') {
  if (currency === 'JPY') {
    return Math.round(amount * USD_TO_JPY)
  }
  return amount
}
