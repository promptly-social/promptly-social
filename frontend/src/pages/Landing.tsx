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
  Users,
  Target,
  Zap,
  Shield,
  Star,
  Quote,
  AlertTriangle,
  BarChart3,
} from "lucide-react";
import { Link, useSearchParams, useNavigate } from "react-router-dom";
import { useEffect } from "react";
import { useToast } from "@/hooks/use-toast";

const Landing = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const { toast } = useToast();

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
              AI LinkedIn Content That Converts
            </Badge>

            {/* IMPACT Headline: [What You Do] + [Outcome] */}
            <h1 className="text-6xl md:text-7xl font-bold text-gray-900 mb-8 leading-tight tracking-tight">
              AI LinkedIn Posts
              <span className="block bg-gradient-to-r from-primary via-secondary to-accent bg-clip-text text-transparent">
                10x Your Engagement
              </span>
            </h1>

            {/* IMPACT Subheadline: We help [Audience] + [Value Prop 1], [Value Prop 2], [Value Prop 3], with [What You Do] */}
            <p className="text-xl text-gray-600 mb-12 leading-relaxed max-w-4xl mx-auto font-light">
              We help busy founders and professionals create authentic LinkedIn
              content, build thought leadership faster, and get 10x more
              engagement with AI that writes in your unique voice.
            </p>

            <div className="flex flex-col sm:flex-row gap-6 justify-center items-center mb-16">
              <Link to="/signup">
                <Button
                  size="lg"
                  className="bg-primary hover:bg-primary/90 text-white text-lg px-10 py-4 shadow-xl"
                >
                  Start Creating Content Today
                  <ArrowRight className="ml-3 w-5 h-5" />
                </Button>
              </Link>
              <p className="text-sm text-gray-500">7-day free trial</p>
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

      {/* EMPATHY Section */}
      <section className="py-24 bg-gradient-to-b from-red-50 to-white border-t border-red-100">
        <div className="max-w-4xl mx-auto px-6 text-center">
          {/* Empathy Headline: [Question] + [Deep Rooted Concern] */}
          <h2 className="text-4xl md:text-5xl font-bold text-gray-900 mb-8 tracking-tight">
            Struggling to Build Your LinkedIn Presence While Running Your
            Business?
          </h2>

          <p className="text-xl text-gray-600 mb-12 max-w-3xl mx-auto font-light leading-relaxed">
            You know LinkedIn is crucial for building thought leadership and
            growing your network. But finding time to create engaging, authentic
            content that actually drives results feels impossible when you're
            juggling everything else.
          </p>

          <div className="bg-white rounded-2xl p-8 shadow-lg border border-red-100">
            <div className="flex items-center justify-center mb-6">
              <AlertTriangle className="w-8 h-8 text-red-500" />
            </div>
            <h3 className="text-2xl font-semibold text-gray-900 mb-4">
              Every day without consistent LinkedIn content is a missed
              opportunity
            </h3>
            <p className="text-gray-600">
              Your competitors are building relationships, establishing
              expertise, and generating leads while your LinkedIn sits silent.
            </p>
          </div>
        </div>
      </section>

      {/* PAIN Section */}
      <section className="py-24 bg-white">
        <div className="max-w-7xl mx-auto px-6">
          <div className="text-center mb-16">
            <h2 className="text-4xl md:text-5xl font-bold text-gray-900 mb-6 tracking-tight">
              The Real Cost of Inconsistent LinkedIn Presence
            </h2>
            <p className="text-xl text-gray-600 max-w-3xl mx-auto">
              Every missed post is lost revenue, lost connections, and lost
              influence in your industry.
            </p>
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-8">
            {[
              {
                icon: BarChart3,
                title: "Lost Revenue",
                description:
                  "Missing out on $50K+ in potential business from LinkedIn connections who never discover your expertise.",
                color: "text-red-600",
                bg: "bg-red-50",
              },
              {
                icon: Clock,
                title: "Wasted Time",
                description:
                  "Spending 3+ hours weekly struggling to create content that gets minimal engagement.",
                color: "text-orange-600",
                bg: "bg-orange-50",
              },
              {
                icon: Users,
                title: "Lost Opportunities",
                description:
                  "Competitors are building the relationships and partnerships that should be yours.",
                color: "text-purple-600",
                bg: "bg-purple-50",
              },
              {
                icon: Target,
                title: "Stalled Growth",
                description:
                  "Your personal brand and business growth hit a ceiling without consistent thought leadership.",
                color: "text-primary",
                bg: "bg-accent/10",
              },
            ].map((pain, index) => (
              <Card
                key={index}
                className={`border-2 border-gray-200 hover:shadow-lg transition-all duration-300 ${pain.bg}`}
              >
                <CardHeader className="text-center">
                  <div
                    className={`w-16 h-16 ${pain.bg} rounded-2xl flex items-center justify-center mb-4 mx-auto`}
                  >
                    <pain.icon className={`w-8 h-8 ${pain.color}`} />
                  </div>
                  <CardTitle className="text-xl text-gray-900 font-semibold mb-3">
                    {pain.title}
                  </CardTitle>
                  <CardDescription className="text-gray-600 leading-relaxed">
                    {pain.description}
                  </CardDescription>
                </CardHeader>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* AUTHORITY Section */}
      <section className="py-24 bg-gradient-to-b from-accent/10 to-background">
        <div className="max-w-7xl mx-auto px-6">
          <div className="text-center mb-16">
            {/* Authority Formula: We Help [Customer Industry] + [Path Forward] */}
            <h2 className="text-4xl md:text-5xl font-bold text-gray-900 mb-6 tracking-tight">
              We Help Busy Founders Build Authentic LinkedIn Presence
            </h2>
            <p className="text-xl text-gray-600 max-w-3xl mx-auto">
              Our AI analyzes your writing style, interests, and content sources
              to create posts that sound exactly like you—because they're
              written in your voice.
            </p>
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
            {[
              {
                icon: PenTool,
                title: "AI Writing Style Analysis",
                description:
                  "Analyzes your existing LinkedIn posts to generate content that sounds authentically you. Never generic, always personal.",
                gradient: "from-primary to-secondary",
              },
              {
                icon: BookOpen,
                title: "Smart Content Sources",
                description:
                  "Automatically pulls insights from your Substack subscriptions and favorite websites to create relevant, timely posts.",
                gradient: "from-green-600 to-green-700",
              },
              {
                icon: Target,
                title: "LinkedIn Algorithm Optimization",
                description:
                  "Built-in engagement strategies: strong hooks, conversation starters, optimal formatting, and strategic hashtags.",
                gradient: "from-purple-600 to-purple-700",
              },
              {
                icon: Zap,
                title: "Daily Personalized Suggestions",
                description:
                  "Wake up to 3-5 ready-to-post suggestions based on your bio, interests, and recent content from your sources.",
                gradient: "from-orange-600 to-orange-700",
              },
              {
                icon: Calendar,
                title: "Schedule Posts",
                description:
                  "Schedule posts with an intuitive calendar interface.",
                gradient: "from-teal-600 to-teal-700",
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
                Transform 5 Minutes Into LinkedIn Growth Engine
              </h3>
              <div className="space-y-6">
                {[
                  "Generate 5 authentic LinkedIn posts daily that sound exactly like you wrote them",
                  "Never run out of content ideas with AI that monitors your favorite sources every day",
                  "Increase engagement 10x with posts optimized for LinkedIn's algorithm",
                  "Build thought leadership without sacrificing time you need for your business",
                  "Post directly to LinkedIn with one click—no copy-paste, no formatting issues",
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
          {/* Action Headline: [Value] + Starts Now */}
          <h2 className="text-4xl md:text-5xl font-bold text-white mb-6 tracking-tight">
            Your LinkedIn Growth Starts Now
          </h2>
          <p className="text-xl text-primary-foreground/80 mb-8 font-light max-w-3xl mx-auto">
            Join forward-thinking founders who are building thought leadership
            and generating leads with AI-powered LinkedIn content.
          </p>

          {/* Cost of Inaction */}
          <div className="bg-primary/20 backdrop-blur-sm border border-accent/30 rounded-2xl p-6 mb-10">
            <p className="text-primary-foreground/90 text-lg">
              <strong>Every day you wait, competitors gain ground.</strong>
              <br />
              Stop losing opportunities to inconsistent LinkedIn presence.
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
