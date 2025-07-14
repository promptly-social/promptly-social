import {
  ActionBarPrimitive,
  ComposerPrimitive,
  ErrorPrimitive,
  MessagePrimitive,
  ThreadPrimitive,
  useMessage,
  type ToolCallContentPart,
} from "@assistant-ui/react";

import type { FC } from "react";
import {
  ArrowDownIcon,
  CheckIcon,
  CopyIcon,
  SendHorizontalIcon,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardFooter,
} from "@/components/ui/card";
import { MarkdownText } from "@/components/assistant-ui/markdown-text";
import { TooltipIconButton } from "@/components/assistant-ui/tooltip-icon-button";
import { useMemo, useRef, useEffect } from "react";
import { usePostScheduling } from "../chat/PostGenerationChatDialog";
import { Badge } from "@/components/ui/badge";

interface GeneratedPost {
  linkedin_post: string;
  topics: string[];
}

export const Thread: FC<{ placeholder?: string; initialText?: string }> = ({
  placeholder = "Write a message...",
  initialText,
}) => {
  return (
    <ThreadPrimitive.Root
      className="bg-background box-border flex h-full flex-col overflow-hidden"
      scroll-lock
      style={{
        ["--thread-max-width" as string]: "42rem",
      }}
    >
      <ThreadPrimitive.Viewport className="flex h-full flex-col items-center overflow-y-scroll scroll-smooth bg-inherit px-4 pt-8">
        <ThreadWelcome initialText={initialText} />

        <ThreadPrimitive.Messages
          components={{
            UserMessage: UserMessage,
            EditComposer: EditComposer,
            AssistantMessage: AssistantMessage,
          }}
        />

        <ThreadPrimitive.If empty={false}>
          <div className="min-h-8 flex-grow" />
        </ThreadPrimitive.If>

        <div className="sticky bottom-0 mt-3 flex w-full max-w-[var(--thread-max-width)] flex-col items-center justify-end rounded-t-lg bg-inherit pb-4">
          <ThreadScrollToBottom />
          <Composer placeholder={placeholder} initialText={initialText} />
        </div>
      </ThreadPrimitive.Viewport>
    </ThreadPrimitive.Root>
  );
};

const ThreadScrollToBottom: FC = () => {
  return (
    <ThreadPrimitive.ScrollToBottom asChild>
      <TooltipIconButton
        tooltip="Scroll to bottom"
        variant="outline"
        className="absolute -top-8 rounded-full disabled:invisible"
      >
        <ArrowDownIcon />
      </TooltipIconButton>
    </ThreadPrimitive.ScrollToBottom>
  );
};

const ThreadWelcome: FC<{ initialText?: string }> = ({ initialText }) => {
  return (
    <ThreadPrimitive.Empty>
      <div className="flex w-full max-w-[var(--thread-max-width)] flex-grow flex-col">
        <div className="flex w-full flex-grow flex-col items-center justify-center">
          <p className="mt-4 font-medium">How can I help you today?</p>
          {initialText && (
            <div className="mt-auto flex flex-wrap justify-center gap-2">
              <ThreadPrimitive.Suggestion
                prompt={initialText}
                method="replace"
                autoSend
                className="bg-transparent hover:bg-muted/80 rounded-lg px-4 py-2 border border-1 text-sm"
              >
                {initialText}
              </ThreadPrimitive.Suggestion>
            </div>
          )}
        </div>
      </div>
    </ThreadPrimitive.Empty>
  );
};

const Composer: FC<{ placeholder: string; initialText?: string }> = ({
  placeholder,
}) => {
  return (
    <ComposerPrimitive.Root className="focus-within:border-ring/20 flex w-full flex-wrap items-end rounded-lg border bg-inherit px-2.5 shadow-sm transition-colors ease-in">
      <ComposerPrimitive.Input
        rows={2}
        autoFocus
        placeholder={placeholder}
        className="placeholder:text-muted-foreground max-h-40 flex-grow resize-none border-none bg-transparent px-2 py-4 text-sm outline-none focus:ring-0 disabled:cursor-not-allowed"
      />
      <ComposerAction />
    </ComposerPrimitive.Root>
  );
};

const ComposerAction: FC = () => {
  return (
    <>
      <ThreadPrimitive.If running={false}>
        <ComposerPrimitive.Send asChild>
          <TooltipIconButton
            tooltip="Send"
            variant="default"
            className="my-2.5 size-8 p-2 transition-opacity ease-in"
          >
            <SendHorizontalIcon />
          </TooltipIconButton>
        </ComposerPrimitive.Send>
      </ThreadPrimitive.If>
      {/* <ThreadPrimitive.If running>
        <ComposerPrimitive.Cancel asChild>
          <TooltipIconButton
            tooltip="Cancel"
            variant="default"
            className="my-2.5 size-8 p-2 transition-opacity ease-in"
          >
            <SquareIcon />
          </TooltipIconButton>
        </ComposerPrimitive.Cancel>
      </ThreadPrimitive.If> */}
    </>
  );
};

const UserMessage: FC = () => {
  return (
    <MessagePrimitive.Root className="grid auto-rows-auto grid-cols-[minmax(72px,1fr)_auto] gap-y-2 [&:where(>*)]:col-start-2 w-full max-w-[var(--thread-max-width)] py-4">
      <UserActionBar />

      <div className="bg-muted text-foreground max-w-[calc(var(--thread-max-width)*0.8)] break-words rounded-3xl px-5 py-2.5 col-start-2 row-start-2">
        <MessagePrimitive.Content />
      </div>
    </MessagePrimitive.Root>
  );
};

const UserActionBar: FC = () => {
  return (
    <ActionBarPrimitive.Root
      hideWhenRunning
      autohide="not-last"
      className="flex flex-col items-end col-start-1 row-start-2 mr-3 mt-2.5"
    ></ActionBarPrimitive.Root>
  );
};

const EditComposer: FC = () => {
  return (
    <ComposerPrimitive.Root className="bg-muted my-4 flex w-full max-w-[var(--thread-max-width)] flex-col gap-2 rounded-xl">
      <ComposerPrimitive.Input className="text-foreground flex h-8 w-full resize-none bg-transparent p-4 pb-0 outline-none" />

      <div className="mx-3 mb-3 flex items-center justify-center gap-2 self-end">
        <ComposerPrimitive.Cancel asChild>
          <Button variant="ghost">Cancel</Button>
        </ComposerPrimitive.Cancel>
        <ComposerPrimitive.Send asChild>
          <Button>Send</Button>
        </ComposerPrimitive.Send>
      </div>
    </ComposerPrimitive.Root>
  );
};

/**
 * The AssistantMessage component is a custom implementation of the
 * {@link MessagePrimitive.Root} component that is used to render messages
 * sent by the assistant. It adds some additional features such as a preview
 * card for tool output and a button to use the preview as a draft for a
 * social media post.
 *
 * @example
 * <AssistantMessage />
 */
const AssistantMessage: FC = () => {
  const message = useMessage();
  const { onSchedule } = usePostScheduling();
  const cardRef = useRef<HTMLDivElement>(null);

  const isToolOutput = useMemo(
    () => message.content[0]?.type === "tool-call",
    [message.content]
  );

  const toolCallContent =
    isToolOutput && message.content[0].type === "tool-call"
      ? (message.content[0] as ToolCallContentPart & { result?: string })
      : null;

  let generatedPost: GeneratedPost | null = null;
  if (toolCallContent?.result) {
    try {
      generatedPost = JSON.parse(toolCallContent.result);
    } catch (e) {
      // Not a json, will be rendered as string
    }
  }

  useEffect(() => {
    if (toolCallContent && cardRef.current) {
      // The thread will scroll to the bottom automatically on new messages.
      // To counteract this for tool calls, we wait a moment and then scroll
      // to the card, overriding the default scroll behavior.
      const timer = setTimeout(() => {
        cardRef.current?.scrollIntoView({
          behavior: "smooth",
          block: "center",
        });
      }, 100); // A small delay is needed to ensure this runs after the default scroll.

      return () => clearTimeout(timer);
    }
  }, [toolCallContent]);

  return (
    <MessagePrimitive.Root className="grid grid-cols-[auto_auto_1fr] grid-rows-[auto_1fr] relative w-full max-w-[var(--thread-max-width)] py-4">
      <div className="text-foreground max-w-[calc(var(--thread-max-width)*0.8)] break-words leading-7 col-span-2 col-start-2 row-start-1 my-1.5">
        {toolCallContent ? (
          generatedPost ? (
            <Card ref={cardRef}>
              <CardHeader>
                <CardTitle className="text-xl">Preview</CardTitle>
              </CardHeader>
              <CardContent className="prose dark:prose-invert text-sm py-4 px-6">
                <p style={{ whiteSpace: "pre-wrap" }}>
                  {generatedPost.linkedin_post}
                </p>
                <div className="not-prose mt-4 flex flex-wrap gap-2">
                  {generatedPost.topics.map((topic) => (
                    <Badge key={topic} variant="secondary">
                      {topic}
                    </Badge>
                  ))}
                </div>
              </CardContent>
              <CardFooter>
                <Button
                  onClick={() => {
                    if (generatedPost?.linkedin_post) {
                      onSchedule(generatedPost.linkedin_post);
                    }
                  }}
                >
                  Use this draft
                </Button>
              </CardFooter>
            </Card>
          ) : (
            <Card ref={cardRef}>
              <CardHeader>
                <CardTitle className="text-xl">Preview</CardTitle>
              </CardHeader>
              <CardContent className="prose dark:prose-invert text-sm py-4 px-6">
                <p style={{ whiteSpace: "pre-wrap" }}>
                  {toolCallContent.result as string}
                </p>
              </CardContent>
              <CardFooter>
                <Button
                  onClick={() => {
                    if (toolCallContent.result) {
                      onSchedule(toolCallContent.result);
                    }
                  }}
                >
                  Use this draft
                </Button>
              </CardFooter>
            </Card>
          )
        ) : (
          <>
            <MessagePrimitive.Content components={{ Text: MarkdownText }} />
            <MessageError />
          </>
        )}
      </div>

      <AssistantActionBar />
    </MessagePrimitive.Root>
  );
};

const MessageError: FC = () => {
  return (
    <MessagePrimitive.Error>
      <ErrorPrimitive.Root className="border-destructive bg-destructive/10 dark:text-red-200 dark:bg-destructive/5 text-destructive mt-2 rounded-md border p-3 text-sm">
        <ErrorPrimitive.Message className="line-clamp-2" />
      </ErrorPrimitive.Root>
    </MessagePrimitive.Error>
  );
};

const AssistantActionBar: FC = () => {
  return (
    <ActionBarPrimitive.Root
      hideWhenRunning
      autohide="not-last"
      autohideFloat="single-branch"
      className="text-muted-foreground flex gap-1 col-start-3 row-start-2 -ml-1 data-[floating]:bg-background data-[floating]:absolute data-[floating]:rounded-md data-[floating]:border data-[floating]:p-1 data-[floating]:shadow-sm"
    >
      <ActionBarPrimitive.Copy asChild>
        <TooltipIconButton tooltip="Copy">
          <MessagePrimitive.If copied>
            <CheckIcon />
          </MessagePrimitive.If>
          <MessagePrimitive.If copied={false}>
            <CopyIcon />
          </MessagePrimitive.If>
        </TooltipIconButton>
      </ActionBarPrimitive.Copy>
    </ActionBarPrimitive.Root>
  );
};
