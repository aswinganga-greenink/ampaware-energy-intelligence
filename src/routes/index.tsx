import { createFileRoute } from "@tanstack/react-router";
import { Navbar } from "@/components/site/Navbar";
import { Hero } from "@/components/site/Hero";
import { Features } from "@/components/site/Features";
import { MonitoringSection } from "@/components/site/MonitoringSection";
import { BillingSection } from "@/components/site/BillingSection";
import { SecuritySection } from "@/components/site/SecuritySection";
import { Testimonials } from "@/components/site/Testimonials";
import { CTASection } from "@/components/site/CTASection";
import { Footer } from "@/components/site/Footer";

export const Route = createFileRoute("/")({
  component: Index,
});

function Index() {
  return (
    <div className="min-h-screen bg-background">
      <Navbar />
      <main>
        <Hero />
        <Features />
        <MonitoringSection />
        <BillingSection />
        <SecuritySection />
        <Testimonials />
        <CTASection />
      </main>
      <Footer />
    </div>
  );
}
