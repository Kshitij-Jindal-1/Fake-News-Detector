import React from 'react'

const Hero = () => {
  return (
    <div className='flex flex-col justify-center items-center text-center px-[16px] md:px-[32px] lg:px-[58px] py-[50px] bg-[var(--bg-secondary)]'>
      <h1 className='text-4xl font-semibold text-[var(--text-primary)]'>Detect Fake News with AI Precision</h1>
      <p className='font-medium text-md text-[var(--text-secondary)] mt-[20px]'>Advanced machine learning algorithm to verify news authenticity</p>
    </div>
  )
}

export default Hero
