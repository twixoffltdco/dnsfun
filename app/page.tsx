import { Hero } from "@/components/Hero";
import { ConnectSection } from "@/components/ConnectSection";
import { MobileSection } from "@/components/MobileSection";
import { SelfHostSection } from "@/components/SelfHostSection";
import { Footer } from "@/components/Footer";

export default function HomePage() {
  return (
    <main className="relative">
      <Hero />
      <ConnectSection />
      <MobileSection />
      <SelfHostSection />
      <Footer />
    </main>
  );
}
