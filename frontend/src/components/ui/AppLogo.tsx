'use client'

import React from 'react'
import { ChefHat } from 'lucide-react'

interface AppLogoProps {
  className?: string
  imageClassName?: string
  logoSrc?: string
  alt?: string
}

const AppLogo: React.FC<AppLogoProps> = ({
  className = '',
  imageClassName = '',
  logoSrc,
  alt = 'App Logo'
}) => {
  const [imageFailed, setImageFailed] = React.useState(false)
  const src = logoSrc || process.env.NEXT_PUBLIC_LOGO_URL || '/logo.png'
  const showImage = !!src && !imageFailed

  return (
    <div
      className={`w-10 h-10 rounded-xl flex items-center justify-center overflow-hidden bg-gradient-to-br from-blue-500 via-orange-500 to-rose-500 shadow-md ${className}`}
      aria-label={alt}
    >
      {showImage ? (
        <img
          src={src}
          alt={alt}
          className={`w-full h-full object-cover ${imageClassName}`}
          onError={() => setImageFailed(true)}
        />
      ) : (
        <ChefHat className="w-5 h-5 text-white" />
      )}
    </div>
  )
}

export default AppLogo
