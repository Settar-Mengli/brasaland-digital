'use client';

import Script from 'next/script';
import { useCallback, useEffect, useRef, useState } from 'react';

import { turnstileSiteKey } from '@/lib/turnstile-widget';

type TurnstileRenderOptions = {
  sitekey: string;
  callback: (token: string) => void;
  'error-callback'?: () => void;
  'expired-callback'?: () => void;
};

declare global {
  interface Window {
    turnstile?: {
      render: (container: HTMLElement, options: TurnstileRenderOptions) => string;
      reset: (widgetId?: string) => void;
      remove: (widgetId?: string) => void;
    };
    onTurnstileLoad?: () => void;
  }
}

type TurnstileChallengeProps = {
  onTokenChange: (token: string | null) => void;
  resetSignal?: number;
};

export default function TurnstileChallenge({
  onTokenChange,
  resetSignal = 0,
}: TurnstileChallengeProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const widgetIdRef = useRef<string | null>(null);
  const [scriptReady, setScriptReady] = useState(false);
  const siteKey = turnstileSiteKey();

  const clearToken = useCallback(() => {
    onTokenChange(null);
  }, [onTokenChange]);

  const renderWidget = useCallback(() => {
    if (!siteKey || !containerRef.current || !window.turnstile) {
      return;
    }
    if (widgetIdRef.current !== null) {
      window.turnstile.remove(widgetIdRef.current);
      widgetIdRef.current = null;
    }
    widgetIdRef.current = window.turnstile.render(containerRef.current, {
      sitekey: siteKey,
      callback: (token: string) => {
        onTokenChange(token);
      },
      'error-callback': clearToken,
      'expired-callback': clearToken,
    });
  }, [clearToken, onTokenChange, siteKey]);

  useEffect(() => {
    window.onTurnstileLoad = () => {
      setScriptReady(true);
    };
    if (window.turnstile) {
      queueMicrotask(() => {
        setScriptReady(true);
      });
    }
    return () => {
      if (window.onTurnstileLoad) {
        delete window.onTurnstileLoad;
      }
    };
  }, []);

  useEffect(() => {
    if (scriptReady) {
      renderWidget();
    }
  }, [renderWidget, scriptReady]);

  useEffect(() => {
    return () => {
      if (widgetIdRef.current !== null && window.turnstile) {
        window.turnstile.remove(widgetIdRef.current);
        widgetIdRef.current = null;
      }
    };
  }, []);

  useEffect(() => {
    if (resetSignal > 0 && widgetIdRef.current && window.turnstile) {
      window.turnstile.reset(widgetIdRef.current);
      clearToken();
    }
  }, [clearToken, resetSignal]);

  if (!siteKey) {
    return null;
  }

  return (
    <>
      <Script
        src="https://challenges.cloudflare.com/turnstile/v0/api.js?onload=onTurnstileLoad"
        strategy="lazyOnload"
      />
      <div ref={containerRef} className="min-h-[65px]" />
    </>
  );
}
