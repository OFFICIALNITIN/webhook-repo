"use client";

import useSWR from "swr";
import { RefreshCw, Github, AlertCircle } from "lucide-react";
import { EventCard, WebhookEvent } from "@/components/EventCard";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

const API_URL = "https://webhook-repo-byyr.onrender.com/api/events";
const POLLING_INTERVAL = 15000;

const fetcher = (url: string) =>
  fetch(url).then((res) => {
    if (!res.ok) {
      throw new Error("Failed to fetch events");
    }
    return res.json();
  });

export default function Home() {
  const { data, error, isLoading, isValidating } = useSWR<WebhookEvent[]>(
    API_URL,
    fetcher,
    {
      refreshInterval: POLLING_INTERVAL,
      revalidateOnFocus: true,
      dedupingInterval: 5000,
    }
  );

  return (
    <div className="min-h-screen bg-background">
      <div className="container mx-auto max-w-3xl px-4 py-8">

        <div className="mb-8 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary text-primary-foreground">
              <Github className="h-5 w-5" />
            </div>
            <div>
              <h1 className="text-2xl font-bold tracking-tight">
                GitHub Webhook Events
              </h1>
              <p className="text-sm text-muted-foreground">
                Real-time activity feed
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <RefreshCw
              className={`h-4 w-4 ${isValidating ? "animate-spin" : ""}`}
            />
            <span>Auto-refresh: 15s</span>
          </div>
        </div>


        {isLoading ? (
          <Card>
            <CardContent className="flex items-center justify-center py-12">
              <div className="flex flex-col items-center gap-3">
                <RefreshCw className="h-8 w-8 animate-spin text-muted-foreground" />
                <p className="text-sm text-muted-foreground">
                  Loading events...
                </p>
              </div>
            </CardContent>
          </Card>
        ) : error ? (
          <Card className="border-destructive/50">
            <CardContent className="flex items-center justify-center py-12">
              <div className="flex flex-col items-center gap-3 text-center">
                <AlertCircle className="h-8 w-8 text-destructive" />
                <div>
                  <p className="font-medium text-destructive">
                    Failed to load events
                  </p>
                  <p className="text-sm text-muted-foreground">
                    Make sure the Flask backend is running at{" "}
                    <code className="rounded bg-muted px-1.5 py-0.5 text-xs">
                      {API_URL}
                    </code>
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        ) : data && data.length > 0 ? (
          <div className="space-y-3">
            {data.map((event, index) => (
              <EventCard key={`${event.timestamp}-${index}`} event={event} />
            ))}
          </div>
        ) : (
          <Card>
            <CardHeader>
              <CardTitle className="text-center text-lg font-medium text-muted-foreground">
                No events yet
              </CardTitle>
            </CardHeader>
            <CardContent className="text-center">
              <p className="text-sm text-muted-foreground">
                Webhook events will appear here when received.
              </p>
            </CardContent>
          </Card>
        )}


        <div className="mt-8 text-center text-xs text-muted-foreground">
          Polling every 15 seconds •{" "}
          {data ? `${data.length} event${data.length !== 1 ? "s" : ""}` : "0 events"}
        </div>
      </div>
    </div>
  );
}
