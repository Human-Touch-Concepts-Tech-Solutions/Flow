'use client'

import { useState } from 'react'
import { ServerStyleSheet, StyleSheetManager } from 'styled-components'
import { useServerInsertedHTML } from 'next/navigation'

export default function StyledComponentsRegistry({ children }) {
  const [sheet] = useState(() => new ServerStyleSheet())

  useServerInsertedHTML(() => {
    const styles = sheet.getStyleElement()
    sheet.instance.clearTag()
    return <>{styles}</>
  })

  if (typeof window !== 'undefined') {
    return <>{children}</>
  }

  return (
    <StyleSheetManager sheet={sheet.instance}>
      {children}
    </StyleSheetManager>
  )
}
