import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  ArrowRight,
  Mic,
  FileText,
  Sparkles,
  Image,
  Calendar,
  Users,
  CheckCircle,
} from "lucide-react";
import { Link, useSearchParams, useNavigate } from "react-router-dom";
import { useEffect } from "react";
import { useToast } from "@/hooks/use-toast";

const Index = () => {
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
              <Sparkles className="w-6 h-6 text-white" />
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
            <Badge className="mb-8 bg-gray-100 text-gray-700 hover:bg-gray-100 border border-gray-200 px-4 py-2 text-sm font-medium">
              AI-Powered Content Creation Platform
            </Badge>

            <h1 className="text-6xl md:text-7xl font-bold text-gray-900 mb-8 leading-tight tracking-tight">
              Content Creation
              <span className="block bg-gradient-to-r from-gray-700 via-gray-800 to-black bg-clip-text text-transparent">
                Reimagined
              </span>
            </h1>

            <p className="text-xl text-gray-600 mb-12 leading-relaxed max-w-3xl mx-auto font-light">
              Transform your ideas into compelling content that reflects your
              unique voice. From concept to publication, streamline your
              workflow with AI that understands your style.
            </p>

            <div className="flex flex-col sm:flex-row gap-6 justify-center items-center mb-16">
              <Link to="/signup">
                <Button
                  size="lg"
                  className="bg-gradient-to-r from-gray-900 to-gray-800 hover:from-gray-800 hover:to-gray-700 text-white text-lg px-10 py-4 shadow-xl"
                >
                  Start Creating
                  <ArrowRight className="ml-3 w-5 h-5" />
                </Button>
              </Link>
            </div>

            {/* Trust Indicators */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-8 pt-8 border-t border-gray-100">
              {[
                { metric: "10K+", label: "Content Pieces Created" },
                { metric: "95%", label: "Time Saved" },
                { metric: "500+", label: "Active Creators" },
                { metric: "4.9/5", label: "User Rating" },
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
              Everything You Need
            </h2>
            <p className="text-xl text-gray-600 max-w-3xl mx-auto font-light">
              A comprehensive suite of AI-powered tools designed for
              professional content creators who demand excellence and
              efficiency.
            </p>
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
            {[
              {
                icon: Mic,
                title: "Voice to Content",
                description:
                  "Transform spoken ideas into structured content with advanced speech recognition and AI processing.",
                gradient: "from-gray-800 to-gray-900",
              },
              {
                icon: FileText,
                title: "Intelligent Outlines",
                description:
                  "Generate comprehensive content structures with key points and logical flow optimization.",
                gradient: "from-gray-700 to-gray-800",
              },
              {
                icon: Sparkles,
                title: "Personal Style AI",
                description:
                  "Learn and replicate your unique writing voice across all content types and platforms.",
                gradient: "from-gray-900 to-black",
              },
              {
                icon: Image,
                title: "Visual Content",
                description:
                  "Create compelling visuals that perfectly complement your written content with AI generation.",
                gradient: "from-gray-600 to-gray-700",
              },
              {
                icon: Calendar,
                title: "Smart Scheduling",
                description:
                  "Optimize posting times and automate publication across multiple platforms.",
                gradient: "from-gray-800 to-gray-900",
              },
              {
                icon: Users,
                title: "Content Management",
                description:
                  "Centralized hub for all your content with approval workflows and version control.",
                gradient: "from-gray-700 to-gray-800",
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
                Why Choose Promptly?
              </h3>
              <div className="space-y-6">
                {[
                  "Professional-grade AI that learns your unique writing style",
                  "Seamless integration with your existing content workflow",
                  "Enterprise-level security and content management",
                  "Time-saving automation without compromising quality",
                ].map((benefit, index) => (
                  <div key={index} className="flex items-start space-x-4">
                    <CheckCircle className="w-6 h-6 text-gray-700 mt-1 flex-shrink-0" />
                    <span className="text-gray-700 text-lg">{benefit}</span>
                  </div>
                ))}
              </div>
            </div>
            <div className="bg-gradient-to-br from-gray-100 to-gray-200 rounded-3xl p-12 text-center">
              <div className="text-5xl font-bold text-gray-900 mb-4">10x</div>
              <div className="text-xl text-gray-700 mb-6">
                Faster Content Creation
              </div>
              <div className="text-gray-600">
                Join thousands of professionals who've transformed their content
                workflow
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-24 bg-gradient-to-r from-gray-900 via-gray-800 to-black">
        <div className="max-w-4xl mx-auto px-6 text-center">
          <h2 className="text-4xl md:text-5xl font-bold text-white mb-6 tracking-tight">
            Ready to Transform Your Content?
          </h2>
          <p className="text-xl text-gray-300 mb-10 font-light max-w-2xl mx-auto">
            Join the next generation of content creators who leverage AI to
            amplify their voice and reach.
          </p>
          <Link to="/signup">
            <Button
              size="lg"
              className="bg-white text-gray-900 hover:bg-gray-100 text-lg px-10 py-4 shadow-xl font-semibold"
            >
              Start Your Journey
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
                <Sparkles className="w-6 h-6 text-white" />
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
            <p>&copy; 2024 Promptly. All rights reserved.</p>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default Index;
