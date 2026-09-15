"use client";

import { Loader2 } from "lucide-react";

import { Button } from "@/components/ui/button";
import { ModelChoice, type DemoModel, type ThinkingLevel } from "./ModelChoice";

type QuickstartPreCallCardProps = {
	isLoading: boolean;
	error: string | null;
	onStartConversation: () => void;
	model: DemoModel;
	onModelChange: (model: DemoModel) => void;
	thinkingLevel: ThinkingLevel;
	onThinkingLevelChange: (level: ThinkingLevel) => void;
};

export function QuickstartPreCallCard({
	isLoading,
	error,
	onStartConversation,
	model,
	onModelChange,
	thinkingLevel,
	onThinkingLevelChange,
}: QuickstartPreCallCardProps) {
	return (
		<div
			className="mx-auto flex w-[min(92vw,26.25rem)] animate-fade-up flex-col items-center rounded-[20px] border border-[#2b2b2b] px-10 py-10 text-center shadow-[0_10px_24px_rgba(0,0,0,0.28)]"
			style={{
				backgroundImage:
					"linear-gradient(164.988deg, rgba(54,54,54,0.2) 1.0596%, rgba(0,0,0,0) 96.089%), linear-gradient(90deg, rgb(16,16,16) 0%, rgb(16,16,16) 100%)",
			}}
		>
			<h1 className="text-[28px] font-medium leading-[1.2] text-white">
				Try Agora&apos;s Voice Agent
			</h1>
			<p className="mt-[14px] text-sm font-medium leading-6 text-muted-foreground">
				Compare two Gemini live voice models in one conversation.
			</p>
			<ModelChoice model={model} onModelChange={onModelChange} thinkingLevel={thinkingLevel} onThinkingLevelChange={onThinkingLevelChange} disabled={isLoading} />

			<Button
				onClick={onStartConversation}
				disabled={isLoading}
				className="mt-6 h-10 w-full rounded-lg border border-primary bg-primary text-sm font-medium text-black hover:border-white hover:bg-white hover:text-black disabled:hover:border-primary disabled:hover:bg-primary disabled:hover:text-black"
				aria-label={
					isLoading
						? "Starting conversation with AI agent"
						: "Start conversation with AI agent"
				}
			>
				{isLoading ? (
					<>
						<Loader2 className="h-4 w-4 animate-spin" />
						Starting...
					</>
				) : (
					"Start Conversation"
				)}
			</Button>
			{error ? <p className="mt-3 text-xs text-destructive">{error}</p> : null}
		</div>
	);
}
