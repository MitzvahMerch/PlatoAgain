// ReactFrontend/app/layout.tsx
import '../styles/globals.css'
import type { ReactNode } from 'react'

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <head />
      <body className="bg-white text-black h-screen">
        {children}
      </body>
    </html>
  )
}