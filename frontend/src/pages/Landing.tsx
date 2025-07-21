import { Button } from "@/components/ui/button";
import {
  Card,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  ArrowRight,
  PenTool,
  Calendar,
  CheckCircle,
  TrendingUp,
  BookOpen,
  Clock,
  Target,
  Zap,
  Shield,
  Brain,
  ChevronLeft,
  ChevronRight,
} from "lucide-react";
import { Link, useSearchParams, useNavigate } from "react-router-dom";
import { useEffect, useState } from "react";
import { useToast } from "@/hooks/use-toast";

const Landing = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const { toast } = useToast();

  // Carousel state
  const [currentSlide, setCurrentSlide] = useState(0);
  const totalSlides = 5;

  // Carousel navigation functions
  const nextSlide = () => {
    setCurrentSlide((prev) => (prev + 1) % totalSlides);
  };

  const prevSlide = () => {
    setCurrentSlide((prev) => (prev - 1 + totalSlides) % totalSlides);
  };

  const goToSlide = (index: number) => {
    setCurrentSlide(index);
  };

  // Auto-cycling carousel
  useEffect(() => {
    const interval = setInterval(() => {
      nextSlide();
    }, 5000); // Change slide every 5 seconds

    return () => clearInterval(interval);
  }, []);

  // Handle OAuth callback with code parameter or verification tokens
  useEffect(() => {
    const code = searchParams.get("code");

    // Check for verification tokens in URL fragment (email verification)
    let hasVerificationTokens = false;
    if (window.location.hash) {
      const fragment = window.location.hash.substring(1);
      const fragmentParams = new URLSearchParams(fragment);
      const accessToken = fragmentParams.get("access_token");
      const type = fragmentParams.get("type");

      if (accessToken && type === "signup") {
        hasVerificationTokens = true;
        console.log("Email verification tokens detected on index page");
        toast({
          title: "Processing Email Verification",
          description: "Please wait while we verify your account...",
        });

        // Redirect to OAuth callback with tokens in fragment
        const callbackUrl = `/auth/callback${window.location.hash}`;
        console.log("Redirecting verification to:", callbackUrl);
        navigate(callbackUrl, { replace: true });
      }
    }

    // Handle OAuth code parameter (Google OAuth)
    if (code && !hasVerificationTokens) {
      toast({
        title: "Processing Authentication",
        description: "Please wait while we complete your sign-in...",
      });

      // Redirect to our OAuth callback handler with all parameters
      const callbackUrl = `/auth/callback?${searchParams.toString()}`;
      navigate(callbackUrl, { replace: true });
    }
  }, [searchParams, navigate, toast]);

  return (
    <div className="min-h-screen bg-background">
      {/* Navigation */}
      <nav className="border-b border-border bg-background/95 backdrop-blur-sm sticky top-0 z-50">
        <div className="flex items-center justify-between p-6 max-w-7xl mx-auto">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 bg-gradient-to-br from-primary via-secondary to-accent rounded-xl flex items-center justify-center shadow-lg">
              <PenTool className="w-6 h-6 text-white" />
            </div>
            <span className="text-2xl font-bold bg-gradient-to-r from-primary to-secondary bg-clip-text text-transparent">
              Promptly
            </span>
          </div>
          <div className="flex items-center space-x-6">
            <Link to="/login">
              <Button
                variant="ghost"
                className="text-muted-foreground hover:text-foreground font-medium"
              >
                Sign In
              </Button>
            </Link>
            <Link to="/signup">
              <Button className="bg-primary hover:bg-primary/90 text-white shadow-lg">
                Start Free Trial
              </Button>
            </Link>
          </div>
        </div>
      </nav>

      {/* Hero Section - IMPACT */}
      <section className="relative overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-br from-gray-50 via-white to-gray-100"></div>
        <div className="relative max-w-7xl mx-auto px-6 pt-20 pb-32">
          <div className="text-center max-w-5xl mx-auto">
            <Badge className="mb-8 bg-accent/20 text-accent-foreground hover:bg-accent/20 border border-accent/30 px-4 py-2 text-sm font-medium">
              AI-Powered LinkedIn Content Creation
            </Badge>

            <h1 className="text-5xl md:text-7xl font-bold text-foreground mb-8 tracking-tight leading-tight">
              Turn Your Ideas Into
              <br />
              <span className="bg-gradient-to-r from-primary via-secondary to-accent bg-clip-text text-transparent">
                Engaging LinkedIn Posts
              </span>
            </h1>

            <p className="text-xl md:text-2xl text-muted-foreground mb-12 font-light max-w-4xl mx-auto leading-relaxed">
              Promptly transforms your content ideas, favorite articles, and
              Substack subscriptions into authentic LinkedIn posts that sound
              exactly like you. Our AI learns your voice and creates daily
              suggestions that drive real engagement.
            </p>

            <div className="flex flex-col items-center space-y-6">
              <Link to="/signup">
                <Button
                  size="lg"
                  className="bg-primary hover:bg-primary/90 text-white text-lg px-10 py-4 shadow-xl"
                >
                  Get Daily Post Suggestions
                  <ArrowRight className="ml-3 w-5 h-5" />
                </Button>
              </Link>
              <p className="text-sm text-gray-500">
                {" "}
                7-day free trial • No credit card required
              </p>
            </div>

            {/* TRUST Indicators */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-8 pt-8 border-t border-gray-100">
              {[
                { metric: "10x", label: "More Engagement", icon: TrendingUp },
                { metric: "5 min", label: "Daily Setup", icon: Clock },
                { metric: "Daily", label: "Fresh Ideas", icon: Zap },
                { metric: "Your Voice", label: "100% Authentic", icon: Shield },
              ].map((stat, index) => (
                <div key={index} className="text-center">
                  <div className="flex items-center justify-center mb-2">
                    <stat.icon className="w-5 h-5 text-primary mr-2" />
                    <div className="text-2xl font-bold text-gray-900">
                      {stat.metric}
                    </div>
                  </div>
                  <div className="text-sm text-gray-600 font-medium">
                    {stat.label}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* EMPATHY & PAIN Section - Carousel */}
      <section className="py-24 bg-gradient-to-b from-red-50 to-white border-t border-red-100">
        <div className="max-w-6xl mx-auto px-6">
          <div className="text-center mb-16">
            <h2 className="text-4xl md:text-5xl font-bold text-gray-900 mb-8 tracking-tight">
              Sound Familiar? 🤔
            </h2>
            <p className="text-xl text-gray-600 max-w-3xl mx-auto font-light leading-relaxed">
              We get it. LinkedIn content creation is... a special kind of
              torture.
            </p>
          </div>

          {/* Carousel Container */}
          <div className="relative overflow-hidden">
            {/* Left Arrow */}
            <button
              onClick={prevSlide}
              className="absolute left-4 top-1/2 -translate-y-1/2 z-10 bg-white/90 hover:bg-white rounded-full p-3 shadow-lg transition-all duration-200 hover:scale-110"
              aria-label="Previous slide"
            >
              <ChevronLeft className="w-6 h-6 text-gray-700" />
            </button>

            {/* Right Arrow */}
            <button
              onClick={nextSlide}
              className="absolute right-4 top-1/2 -translate-y-1/2 z-10 bg-white/90 hover:bg-white rounded-full p-3 shadow-lg transition-all duration-200 hover:scale-110"
              aria-label="Next slide"
            >
              <ChevronRight className="w-6 h-6 text-gray-700" />
            </button>

            <div 
              className="flex transition-transform duration-500 ease-in-out"
              style={{ transform: `translateX(-${currentSlide * 100}%)` }}
            >
              {[
                {
                  icon: "😤",
                  title: "Are you jealous of Gary from Accounting?",
                  description:
                    "He posts more often than you on LinkedIn and somehow gets 50+ likes on his 'Monday Motivation' posts. GARY. From ACCOUNTING.",
                  bg: "bg-orange-50",
                  border: "border-orange-200",
                },
                {
                  icon: "⏰",
                  title: "Staring at the blank post box for 47 minutes?",
                  description:
                    "You opened LinkedIn to post something insightful. Three cat videos and a scroll through your ex-colleague's vacation photos later, you close the tab.",
                  bg: "bg-purple-50",
                  border: "border-purple-200",
                },
                {
                  icon: "🎭",
                  title: "Your last post got 3 likes (including your mom)?",
                  description:
                    "You spent 2 hours crafting what you thought was pure LinkedIn gold. Your mom, your business partner, and... that's it. Even the LinkedIn algorithm ghosted you.",
                  bg: "bg-blue-50",
                  border: "border-blue-200",
                },
                {
                  icon: "🤖",
                  title: "Tried ChatGPT but it sounds like a robot?",
                  description:
                    "'Excited to share insights on synergistic paradigm shifts!' No human has ever talked like this. Your audience can smell the AI from a mile away.",
                  bg: "bg-green-50",
                  border: "border-green-200",
                },
                {
                  icon: "📈",
                  title: "Watching competitors build their empire?",
                  description:
                    "While you're perfecting that one post for the 15th time, your competitors are out there building relationships, closing deals, and becoming industry thought leaders.",
                  bg: "bg-red-50",
                  border: "border-red-200",
                },
              ].map((item, index) => (
                <div key={index} className="w-full flex-shrink-0 px-4">
                  <Card
                    className={`${item.bg} border-2 ${item.border} hover:shadow-xl transition-all duration-300 mx-auto max-w-2xl`}
                  >
                    <CardHeader className="text-center p-8">
                      <div className="text-6xl mb-6">{item.icon}</div>
                      <CardTitle className="text-2xl text-gray-900 font-bold mb-4">
                        {item.title}
                      </CardTitle>
                      <CardDescription className="text-gray-700 text-lg leading-relaxed">
                        {item.description}
                      </CardDescription>
                    </CardHeader>
                  </Card>
                </div>
              ))}
            </div>
            
            {/* Carousel Navigation Dots */}
            <div className="flex justify-center mt-8 space-x-2">
              {[0, 1, 2, 3, 4].map((index) => (
                <button
                  key={index}
                  className={`w-3 h-3 rounded-full transition-colors duration-200 ${
                    currentSlide === index ? 'bg-primary' : 'bg-gray-300 hover:bg-primary/70'
                  }`}
                  onClick={() => goToSlide(index)}
                  aria-label={`Go to slide ${index + 1}`}
                />
              ))}
            </div>
          </div>

          {/* Bottom CTA */}
          <div className="text-center mt-12">
            <div className="bg-white rounded-2xl p-8 shadow-lg border border-red-200 max-w-3xl mx-auto">
              <h3 className="text-2xl font-bold text-gray-900 mb-4">
                Stop the LinkedIn Struggle Bus 🚌💨
              </h3>
              <p className="text-gray-600 text-lg">
                What if you could wake up to personalized, authentic LinkedIn
                posts that actually sound like you wrote them?
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* AUTHORITY Section */}
      <section className="py-24 bg-gradient-to-b from-accent/10 to-background">
        <div className="max-w-7xl mx-auto px-6">
          <div className="text-center mb-16">
            <h2 className="text-4xl md:text-5xl font-bold text-gray-900 mb-6 tracking-tight">
              AI That Actually Understands Your Voice
            </h2>
            <p className="text-xl text-gray-600 max-w-3xl mx-auto">
              From content ideas to published posts - Promptly handles your
              entire LinkedIn content workflow. Our AI learns your writing style
              and creates daily suggestions that sound authentically like you.
            </p>
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
            {[
              {
                icon: Zap,
                title: "Daily AI Suggestions",
                description:
                  "Get personalized post suggestions every day based on your interests, favorite websites, and Substack subscriptions.",
                gradient: "from-primary to-secondary",
              },
              {
                icon: PenTool,
                title: "Learns Your Voice",
                description:
                  "Our AI analyzes your writing style and creates posts that sound authentically like you - not generic AI content.",
                gradient: "from-green-600 to-green-700",
              },
              {
                icon: BookOpen,
                title: "Content Idea Bank",
                description:
                  "Drop in article URLs, jot down quick notes, or brainstorm with AI to never run out of content ideas.",
                gradient: "from-purple-600 to-purple-700",
              },
              {
                icon: Calendar,
                title: "Smart Scheduling",
                description:
                  "Schedule posts for optimal times or publish immediately. Handle drafts, scheduled posts, and published content in one place.",
                gradient: "from-orange-600 to-orange-700",
              },
              {
                icon: Target,
                title: "Topic Preferences",
                description:
                  "Tell us what you like to write about and which websites you follow. We'll create relevant content suggestions.",
                gradient: "from-teal-600 to-teal-700",
              },
              {
                icon: Brain,
                title: "Continuous Learning",
                description:
                  "The more you use Promptly, the better it gets at understanding your preferences and creating engaging content.",
                gradient: "from-blue-600 to-blue-700",
              },
            ].map((feature, index) => (
              <Card
                key={index}
                className="group border border-gray-200 shadow-sm hover:shadow-xl transition-all duration-500 bg-white hover:bg-gray-50/50"
              >
                <CardHeader className="pb-4">
                  <div
                    className={`w-14 h-14 bg-gradient-to-br ${feature.gradient} rounded-2xl flex items-center justify-center mb-6 group-hover:scale-110 transition-transform duration-300 shadow-lg`}
                  >
                    <feature.icon className="w-7 h-7 text-white" />
                  </div>
                  <CardTitle className="text-xl text-gray-900 font-semibold mb-3">
                    {feature.title}
                  </CardTitle>
                  <CardDescription className="text-gray-600 leading-relaxed">
                    {feature.description}
                  </CardDescription>
                </CardHeader>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* Benefits Section */}
      <section className="py-24 bg-gradient-to-b from-gray-50 to-white">
        <div className="max-w-7xl mx-auto px-6">
          <div className="grid lg:grid-cols-2 gap-16 items-center">
            <div>
              <h3 className="text-4xl font-bold text-gray-900 mb-8 tracking-tight">
                From Content Ideas to Published Posts
              </h3>
              <div className="space-y-6">
                {[
                  "Get daily personalized post suggestions based on your interests and favorite content sources",
                  "AI learns your writing style to create posts that sound authentically like you",
                  "Transform article URLs and quick notes into engaging LinkedIn content",
                  "Schedule posts or publish immediately with intuitive content management",
                  "Build consistent LinkedIn presence without spending hours writing",
                ].map((benefit, index) => (
                  <div key={index} className="flex items-start space-x-4">
                    <CheckCircle className="w-6 h-6 text-green-600 mt-1 flex-shrink-0" />
                    <span className="text-gray-700 text-lg">{benefit}</span>
                  </div>
                ))}
              </div>
            </div>
            <div className="bg-gradient-to-br from-accent/10 to-accent/20 rounded-3xl p-12 text-center">
              <div className="text-6xl font-bold text-primary mb-4">5 min</div>
              <div className="text-xl text-secondary mb-6">
                Daily Time Investment
              </div>
              <div className="text-primary text-lg leading-relaxed">
                Spend 5 minutes reviewing and publishing.
                <br />
                <strong>Get 10x the results of hours of manual work.</strong>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ACTION Section */}
      <section className="py-24 bg-gradient-to-r from-primary via-secondary to-accent">
        <div className="max-w-4xl mx-auto px-6 text-center">
          <h2 className="text-4xl md:text-5xl font-bold text-white mb-6 tracking-tight">
            Start Creating Authentic LinkedIn Content Today
          </h2>
          <p className="text-xl text-primary-foreground/80 mb-8 font-light max-w-3xl mx-auto">
            Join professionals who are building their LinkedIn presence with AI
            that learns their voice and creates personalized content suggestions
            every day.
          </p>

          <div className="bg-primary/20 backdrop-blur-sm border border-accent/30 rounded-2xl p-6 mb-10">
            <p className="text-primary-foreground/90 text-lg">
              <strong>Stop staring at blank pages.</strong>
              <br />
              Get daily content suggestions that sound exactly like you.
            </p>
          </div>

          <div className="flex flex-col sm:flex-row gap-6 justify-center items-center">
            <Link to="/signup">
              <Button
                size="lg"
                className="bg-white text-primary hover:bg-muted text-lg px-12 py-4 shadow-xl font-semibold"
              >
                Start Your 7-Day Free Trial
                <ArrowRight className="ml-3 w-5 h-5" />
              </Button>
            </Link>
          </div>

          <p className="text-primary-foreground/70 text-sm mt-6">
            Cancel anytime • Setup in under 5 minutes
          </p>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-gray-100 bg-white">
        <div className="max-w-7xl mx-auto px-6 py-16">
          <div className="flex flex-col md:flex-row justify-between items-center">
            <div className="flex items-center space-x-3 mb-8 md:mb-0">
              <div className="w-10 h-10 bg-gradient-to-br from-primary via-secondary to-accent rounded-xl flex items-center justify-center shadow-lg">
                <PenTool className="w-6 h-6 text-white" />
              </div>
              <span className="text-2xl font-bold bg-gradient-to-r from-primary to-secondary bg-clip-text text-transparent">
                Promptly
              </span>
            </div>
            <div className="flex space-x-8 text-gray-600">
              <a
                href="/privacy-policy.html"
                target="_blank"
                rel="noopener noreferrer"
                className="hover:text-gray-900 transition-colors font-medium"
              >
                Privacy Policy
              </a>
              <a
                href="/terms-of-service.html"
                target="_blank"
                rel="noopener noreferrer"
                className="hover:text-gray-900 transition-colors font-medium"
              >
                Terms of Service
              </a>
              <a
                href="mailto:support@promptly.social"
                className="hover:text-gray-900 transition-colors font-medium"
              >
                Support
              </a>
            </div>
          </div>
          <div className="mt-8 pt-8 border-t border-gray-100 text-center text-gray-500">
            <p>&copy; 2025 Promptly AI, LLC. All rights reserved.</p>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default Landing;
