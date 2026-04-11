import React from 'react'
import Cards from './Cards'
import { assets } from '../assets/assets'

const WorkCards = () => {
  return (
    <div className='flex flex-col justify-center items-center text-center px-[16px] md:px-[32px] lg:px-[58px] mt-[88px] mb-[30px]'>
      <div className='grid grid-cols-1 gap-8 md:grid-cols-3 max-w-[1250px]  w-[100%]'>
        <Cards image={assets.icon1} heading={"Content Analysis"} content={"Our AI examines the text structure, language patterns, and content authenticity"} />
        <Cards image={assets.icon2} heading={"Pattern Recognition"} content={"Advanced algorithms detect common indicators of fake news"} />
        <Cards image={assets.icon3} heading={"Cross-Verification"} content={"Content is compared against verified news sources and databases"} />
      </div>
    </div>
  )
}

export default WorkCards
