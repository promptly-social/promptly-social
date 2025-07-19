import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { useAuth } from "@/contexts/AuthContext";
import { useProfile } from "@/contexts/ProfileContext";

export const PostCardHeader = () => {
  const { user } = useAuth();
  const { linkedinConnection } = useProfile();

  const userAvatar = linkedinConnection?.connection_data?.avatar_url || "";
  const userName = user?.full_name || user?.email || "User";
  const userHeadline = "Promptly User";

  return (
    <div className="flex items-center gap-3">
      <Avatar>
        <AvatarImage src={userAvatar} alt={userName} />
        <AvatarFallback>{userName.charAt(0)}</AvatarFallback>
      </Avatar>
      <div className="flex-1">
        <p className="font-semibold text-sm">{userName}</p>
        <p className="text-xs text-gray-500">{userHeadline}</p>
      </div>
    </div>
  );
};
