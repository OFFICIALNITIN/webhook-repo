"use client";

import { GitCommit, GitPullRequest, GitMerge, LucideIcon } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";

export interface WebhookEvent {
  author: string;
  action: "PUSH" | "PULL_REQUEST" | "MERGE";
  from_branch?: string;
  to_branch: string;
  timestamp: string;
}

interface EventConfig {
  icon: LucideIcon;
  label: string;
  badgeClass: string;
  iconClass: string;
  getMessage: (event: WebhookEvent) => string;
}

const eventConfigs: Record<WebhookEvent["action"], EventConfig> = {
  PUSH: {
    icon: GitCommit,
    label: "Push",
    badgeClass: "bg-emerald-500/15 text-emerald-600 border-emerald-500/20",
    iconClass: "text-emerald-500",
    getMessage: (event) =>
      `${event.author} pushed to ${event.to_branch} on ${event.timestamp}`,
  },
  PULL_REQUEST: {
    icon: GitPullRequest,
    label: "Pull Request",
    badgeClass: "bg-purple-500/15 text-purple-600 border-purple-500/20",
    iconClass: "text-purple-500",
    getMessage: (event) =>
      `${event.author} submitted a pull request from ${event.from_branch} to ${event.to_branch} on ${event.timestamp}`,
  },
  MERGE: {
    icon: GitMerge,
    label: "Merge",
    badgeClass: "bg-orange-500/15 text-orange-600 border-orange-500/20",
    iconClass: "text-orange-500",
    getMessage: (event) =>
      `${event.author} merged branch ${event.from_branch} to ${event.to_branch} on ${event.timestamp}`,
  },
};

interface EventCardProps {
  event: WebhookEvent;
}

export function EventCard({ event }: EventCardProps) {
  const config = eventConfigs[event.action];
  const Icon = config.icon;

  return (
    <Card className="transition-all duration-200 hover:shadow-md">
      <CardContent className="flex items-start gap-4 py-4">
        <div
          className={cn(
            "flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-muted",
            config.iconClass
          )}
        >
          <Icon className="h-5 w-5" />
        </div>
        <div className="flex flex-1 flex-col gap-2">
          <div className="flex items-center gap-2">
            <Badge className={cn("border", config.badgeClass)}>
              {config.label}
            </Badge>
          </div>
          <p className="text-sm text-muted-foreground leading-relaxed">
            {config.getMessage(event)}
          </p>
        </div>
      </CardContent>
    </Card>
  );
}
