import Header from './_components/Header';
import HeroSection from './_components/HeroSection';
import StorySection from './_components/StorySection';
import FeaturesSection from './_components/FeaturesSection';
import LocationsSection from './_components/LocationsSection';
import BrasaPointsSection from './_components/BrasaPointsSection';
import ContactSection from './_components/ContactSection';
import Footer from './_components/Footer';
import GuestChatWidget from './_components/GuestChatWidget';

export default function HomePage() {
  return (
    <>
      <Header />
      <main id="main-content">
        <HeroSection />
        <StorySection />
        <FeaturesSection />
        <LocationsSection />
        <BrasaPointsSection />
        <ContactSection />
      </main>
      <GuestChatWidget />
      <Footer />
    </>
  );
}
