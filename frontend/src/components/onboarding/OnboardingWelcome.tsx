import React from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { PlayCircle, RotateCcw, Users } from 'lucide-react';
import { useOnboardingContext } from './OnboardingProvider';
import { useOnboarding } from '@/hooks/useOnboarding';

interface OnboardingWelcomeProps {
  /**
   * Show welcome card for new users
   */
  showWelcomeCard?: boolean;
  /**
   * Custom welcome message
   */
  welcomeMessage?: string;
  /**
   * Show admin controls for testing
   */
  showAdminControls?: boolean;
}

/**
 * Welcome component that provides manual onboarding triggers
 * and welcome messaging for new users
 */
export const OnboardingWelcome: React.FC<OnboardingWelcomeProps> = ({
  showWelcomeCard = true,
  welcomeMessage = "Welcome to Promptly Social Scribe! Let's get you set up with a quick tour.",
  showAdminControls = false,
}) => {
  const { setShowModal } = useOnboardingContext();
  const { progress, resetOnboarding, loading } = useOnboarding();

  const startOnboarding = () => {
    setShowModal(true);
  };

  const restartOnboarding = async () => {
    try {
      await resetOnboarding();
      setShowModal(true);
    } catch (error) {
      console.error('Failed to restart onboarding:', error);
    }
  };

  // Don't show welcome card if onboarding is completed
  if (!showWelcomeCard || (progress && progress.is_completed)) {
    return null;
  }

  return (
    <div className="space-y-4">
      {/* Welcome Card for New Users */}
      {(!progress || (!progress.is_completed && !progress.is_skipped)) && (
        <Card className="border-blue-200 bg-blue-50/50">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-blue-900">
              <Users className="h-5 w-5" />
              Welcome to Promptly Social Scribe!
            </CardTitle>
            <CardDescription className="text-blue-700">
              {welcomeMessage}
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Button 
              onClick={startOnboarding}
              className="bg-blue-600 hover:bg-blue-700 text-white"
              disabled={loading}
            >
              <PlayCircle className="h-4 w-4 mr-2" />
              Start Getting Started Tour
            </Button>
          </CardContent>
        </Card>
      )}

      {/* Admin Controls for Testing */}
      {showAdminControls && (
        <Card className="border-gray-200">
          <CardHeader>
            <CardTitle className="text-sm font-medium text-gray-700">
              Onboarding Controls
            </CardTitle>
            <CardDescription className="text-xs text-gray-500">
              Development and testing controls
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-2">
            <div className="flex gap-2">
              <Button 
                variant="outline" 
                size="sm"
                onClick={startOnboarding}
                disabled={loading}
              >
                <PlayCircle className="h-3 w-3 mr-1" />
                Show Modal
              </Button>
              <Button 
                variant="outline" 
                size="sm"
                onClick={restartOnboarding}
                disabled={loading}
              >
                <RotateCcw className="h-3 w-3 mr-1" />
                Reset & Restart
              </Button>
            </div>
            {progress && (
              <div className="text-xs text-gray-500 mt-2">
                Status: {progress.is_completed ? 'Completed' : progress.is_skipped ? 'Skipped' : `Step ${progress.current_step}/6`}
              </div>
            )}
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default OnboardingWelcome;
