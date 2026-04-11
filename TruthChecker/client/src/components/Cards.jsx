import React from 'react'

const Cards = ({image, heading, content}) => {
  return (
    <div className='bg-[var(--bg-secondary)] p-[20px] flex flex-col justify-start items-center rounded-xl border border-[var(--border-color)]'>
      <img src={image} alt="" className='w-[39px] h-auto' />
      <h3 className='text-[18px] leading-[24px] font-semibold mt-[10px] text-[var(--text-primary)]'>{heading}</h3>
      <p className='text-sm text-[var(--text-secondary)] leading-[16px] mt-[12px]'>{content}</p>
    </div>
  )
}

export default Cards
