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
  FileText,
  PenTool,
  Calendar,
  CheckCircle,
  TrendingUp,
  BookOpen,
  Globe,
} from "lucide-react";
import { Link, useSearchParams, useNavigate } from "react-router-dom";
import { useEffect } from "react";
import { useToast } from "@/hooks/use-toast";

const Landing = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const { toast } = useToast();

  // Handle OAuth callback with code parameter
  useEffect(() => {
    const code = searchParams.get("code");
    if (code) {
      console.log("OAuth code detected on index page:", code);
      toast({
        title: "Processing Authentication",
        description: "Please wait while we complete your sign-in...",
      });

      // Redirect to our OAuth callback handler with all parameters
      const callbackUrl = `/auth/callback?${searchParams.toString()}`;
      console.log("Redirecting to:", callbackUrl);
      navigate(callbackUrl, { replace: true });
    }
  }, [searchParams, navigate, toast]);

  return (
    <div className="min-h-screen bg-white">
      {/* Navigation */}
      <nav className="border-b border-gray-100 bg-white/95 backdrop-blur-sm sticky top-0 z-50">
        <div className="flex items-center justify-between p-6 max-w-7xl mx-auto">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 bg-gradient-to-br from-gray-900 via-gray-800 to-black rounded-xl flex items-center justify-center shadow-lg">
              <PenTool className="w-6 h-6 text-white" />
            </div>
            <span className="text-2xl font-bold bg-gradient-to-r from-gray-900 to-gray-700 bg-clip-text text-transparent">
              Promptly
            </span>
          </div>
          <div className="flex items-center space-x-6">
            <Link to="/login">
              <Button
                variant="ghost"
                className="text-gray-600 hover:text-gray-900 font-medium"
              >
                Sign In
              </Button>
            </Link>
            <Link to="/signup">
              <Button className="bg-gradient-to-r from-gray-900 to-gray-800 hover:from-gray-800 hover:to-gray-700 text-white shadow-lg">
                Get Started
              </Button>
            </Link>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="relative overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-br from-gray-50 via-white to-gray-100"></div>
        <div className="relative max-w-7xl mx-auto px-6 pt-20 pb-32">
          <div className="text-center max-w-5xl mx-auto">
            <Badge className="mb-8 bg-blue-100 text-blue-700 hover:bg-blue-100 border border-blue-200 px-4 py-2 text-sm font-medium">
              AI-Powered LinkedIn Content Engine
            </Badge>

            <h1 className="text-6xl md:text-7xl font-bold text-gray-900 mb-8 leading-tight tracking-tight">
              LinkedIn Growth
              <span className="block bg-gradient-to-r from-blue-600 via-blue-700 to-blue-800 bg-clip-text text-transparent">
                Made Simple
              </span>
            </h1>

            <p className="text-xl text-gray-600 mb-12 leading-relaxed max-w-3xl mx-auto font-light">
              Transform your professional presence on LinkedIn. Generate
              personalized posts that reflect your unique voice, schedule
              content effortlessly, and maximize engagement with AI that
              understands LinkedIn best practices.
            </p>

            <div className="flex flex-col sm:flex-row gap-6 justify-center items-center mb-16">
              <Link to="/signup">
                <Button
                  size="lg"
                  className="bg-gradient-to-r from-blue-600 to-blue-700 hover:from-blue-700 hover:to-blue-800 text-white text-lg px-10 py-4 shadow-xl"
                >
                  Join Early Access
                  <ArrowRight className="ml-3 w-5 h-5" />
                </Button>
              </Link>
            </div>

            {/* Trust Indicators */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-8 pt-8 border-t border-gray-100">
              {[
                { metric: "10x", label: "More Engagement" },
                { metric: "30 min", label: "Weekly Time Investment" },
                { metric: "Daily", label: "Content Suggestions" },
                { metric: "Your Voice", label: "Authentic & Personal" },
              ].map((stat, index) => (
                <div key={index} className="text-center">
                  <div className="text-2xl font-bold text-gray-900">
                    {stat.metric}
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

      {/* Features Section */}
      <section className="py-24 bg-gradient-to-b from-white to-gray-50">
        <div className="max-w-7xl mx-auto px-6">
          <div className="text-center mb-20">
            <h2 className="text-4xl md:text-5xl font-bold text-gray-900 mb-6 tracking-tight">
              Everything You Need for LinkedIn Success
            </h2>
            <p className="text-xl text-gray-600 max-w-3xl mx-auto font-light">
              Designed specifically for busy professionals and founders who want
              to build their LinkedIn presence without spending hours crafting
              posts.
            </p>
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
            {[
              {
                icon: PenTool,
                title: "Personal Writing Style AI",
                description:
                  "Analyzes your existing LinkedIn posts, bio, and writing samples to generate content that sounds authentically you.",
                gradient: "from-blue-600 to-blue-700",
              },
              {
                icon: Calendar,
                title: "Smart Scheduling",
                description:
                  "Automatically schedule posts at optimal times for your audience and maintain consistent LinkedIn presence.",
                gradient: "from-green-600 to-green-700",
              },
              {
                icon: BookOpen,
                title: "Content Source Integration",
                description:
                  "Pull insights from your Substack subscriptions, favorite websites, and industry topics to inspire relevant posts.",
                gradient: "from-purple-600 to-purple-700",
              },
              {
                icon: TrendingUp,
                title: "LinkedIn Best Practices",
                description:
                  "Built-in optimization for LinkedIn's algorithm, using proven engagement strategies and formatting techniques.",
                gradient: "from-orange-600 to-orange-700",
              },
              {
                icon: FileText,
                title: "Daily Post Suggestions",
                description:
                  "Wake up to personalized content ideas based on your interests, industry trends, and recent activities.",
                gradient: "from-indigo-600 to-indigo-700",
              },
              {
                icon: Globe,
                title: "Multi-Source Learning",
                description:
                  "Combines your bio, interests, website content, and professional background for comprehensive personalization.",
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
      <section className="py-24 bg-white">
        <div className="max-w-7xl mx-auto px-6">
          <div className="grid lg:grid-cols-2 gap-16 items-center">
            <div>
              <h3 className="text-4xl font-bold text-gray-900 mb-8 tracking-tight">
                Perfect for Busy Professionals
              </h3>
              <div className="space-y-6">
                {[
                  "Generate authentic LinkedIn posts that reflect your unique professional voice",
                  "Save hours weekly while maintaining consistent LinkedIn presence",
                  "Increase engagement with AI-optimized content following LinkedIn best practices",
                  "Never run out of content ideas with daily personalized suggestions",
                  "Seamlessly integrate your existing content sources and expertise",
                ].map((benefit, index) => (
                  <div key={index} className="flex items-start space-x-4">
                    <CheckCircle className="w-6 h-6 text-blue-600 mt-1 flex-shrink-0" />
                    <span className="text-gray-700 text-lg">{benefit}</span>
                  </div>
                ))}
              </div>
            </div>
            <div className="bg-gradient-to-br from-blue-50 to-blue-100 rounded-3xl p-12 text-center">
              <div className="text-5xl font-bold text-blue-700 mb-4">
                30 min
              </div>
              <div className="text-xl text-blue-800 mb-6">
                Weekly Time Investment
              </div>
              <div className="text-blue-700">
                Maintain a strong LinkedIn presence with just 30 minutes of
                setup and review time per week
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-24 bg-gradient-to-r from-blue-600 via-blue-700 to-blue-800">
        <div className="max-w-4xl mx-auto px-6 text-center">
          <h2 className="text-4xl md:text-5xl font-bold text-white mb-6 tracking-tight">
            Ready to Amplify Your LinkedIn Presence?
          </h2>
          <p className="text-xl text-blue-100 mb-10 font-light max-w-2xl mx-auto">
            Join forward-thinking professionals and founders who are building
            their thought leadership on LinkedIn with AI-powered content
            creation.
          </p>
          <Link to="/signup">
            <Button
              size="lg"
              className="bg-white text-blue-700 hover:bg-gray-100 text-lg px-10 py-4 shadow-xl font-semibold"
            >
              Start Growing Your LinkedIn
              <ArrowRight className="ml-3 w-5 h-5" />
            </Button>
          </Link>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-gray-100 bg-white">
        <div className="max-w-7xl mx-auto px-6 py-16">
          <div className="flex flex-col md:flex-row justify-between items-center">
            <div className="flex items-center space-x-3 mb-8 md:mb-0">
              <div className="w-10 h-10 bg-gradient-to-br from-gray-900 via-gray-800 to-black rounded-xl flex items-center justify-center shadow-lg">
                <PenTool className="w-6 h-6 text-white" />
              </div>
              <span className="text-2xl font-bold bg-gradient-to-r from-gray-900 to-gray-700 bg-clip-text text-transparent">
                Promptly
              </span>
            </div>
            <div className="flex space-x-8 text-gray-600">
              <a
                href="#"
                className="hover:text-gray-900 transition-colors font-medium"
              >
                Privacy Policy
              </a>
              <a
                href="#"
                className="hover:text-gray-900 transition-colors font-medium"
              >
                Terms of Service
              </a>
              <a
                href="#"
                className="hover:text-gray-900 transition-colors font-medium"
              >
                Support
              </a>
            </div>
          </div>
          <div className="mt-8 pt-8 border-t border-gray-100 text-center text-gray-500">
            <p>&copy; 2025 Impolester, LLC. All rights reserved.</p>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default Landing;
