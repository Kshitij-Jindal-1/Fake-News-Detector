import React from 'react';
import Navbar from '../components/Navbar';
import NewsTicker from '../components/NewsTicker';
import Hero from '../components/Hero';
import Input from '../components/Input';
import WorkCards from '../components/WorkCards';
import Footer from '../components/Footer';

/**
 * Home Page - Main landing page with the fake news checker
 */
const HomePage = () => {
  return (
    <>
      <Navbar />
      <NewsTicker />
      <Hero />
      <Input />
      <WorkCards />
      <Footer />
    </>
  );
};

export default HomePage;
