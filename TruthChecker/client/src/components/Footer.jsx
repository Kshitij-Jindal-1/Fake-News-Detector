import React from 'react'
import { assets } from '../assets/assets'

const Footer = () => {
  return (
    <div className='flex flex-col justify-between md:flex-row items-center text-center px-[16px] md:px-[32px] lg:px-[58px] bg-[var(--bg-secondary)] mt-[120px] py-[30px]'>
      <img src={assets.logo} alt="" className='w-[122px] h-[24px]'/>
      <p className='text-sm font-medium text-[var(--text-secondary)]'>Made By Kshitij,Arpan,Apoorv,Mayank.</p>
    </div>
  )
}

export default Footer
