// packages/chatbot-ui/src/branding/branding-store.ts

import { type BrandingConfig, type WidgetState } from '../types';
import { DEFAULT_ENVOY_THEME } from './default-theme';
import { BrandingValidator } from './branding-validator';

export type StoreListener = (config: BrandingConfig, state: WidgetState) => void;

export class BrandingStore {
  private config: BrandingConfig = { ...DEFAULT_ENVOY_THEME };
  private state: WidgetState = 'idle';
  private listeners: Set<StoreListener> = new Set();
  private lastFetchedBotId: string | null = null;

  public addListener(listener: StoreListener) {
    this.listeners.add(listener);
    // Trigger immediately with current values
    listener(this.config, this.state);
  }

  public removeListener(listener: StoreListener) {
    this.listeners.delete(listener);
  }

  public getConfig(): BrandingConfig {
    return this.config;
  }

  public getState(): WidgetState {
    return this.state;
  }

  /**
   * Reset store and force reload branding configuration
   */
  public async loadBranding(botId: string, apiBase: string, force = false) {
    if (!botId) {
      this.state = 'error';
      this.notify();
      return;
    }

    if (this.lastFetchedBotId === botId && this.state === 'connected' && !force) {
      // Prevent redundant fetches
      return;
    }

    this.state = 'loading';
    this.notify();
    this.lastFetchedBotId = botId;

    try {
      const response = await fetch(`${apiBase}/api/v1/products/${botId}`);
      if (response.ok) {
        const data = await response.json();
        // Check if ui_theme_config is a string and parse it, or check if it's already an object
        let rawTheme = data.ui_theme_config || {};
        if (typeof rawTheme === 'string') {
          try {
            rawTheme = JSON.parse(rawTheme);
          } catch {
            rawTheme = {};
          }
        }
        
        // Merge top-level properties from product data (e.g. name, logos) into configuration
        const rawConfig = {
          colors: rawTheme.colors || rawTheme || {},
          typography: rawTheme.typography || rawTheme || {},
          layout: rawTheme.layout || rawTheme || {},
          assets: {
            companyLogo: rawTheme.companyLogo || data.logoUrl || '',
            chatAvatar: rawTheme.chatAvatar || '',
            botAvatar: rawTheme.botAvatar || '',
            launcherIcon: rawTheme.launcherIcon || '',
            headerIcon: rawTheme.headerIcon || ''
          },
          content: {
            widgetTitle: rawTheme.widgetTitle || data.name || '',
            welcomeMessage: rawTheme.welcomeMessage || '',
            placeholderText: rawTheme.placeholderText || '',
            offlineMessage: rawTheme.offlineMessage || '',
            errorMessage: rawTheme.errorMessage || '',
            typingIndicatorText: rawTheme.typingIndicatorText || ''
          },
          featureFlags: rawTheme.featureFlags || rawTheme || {}
        };

        this.config = BrandingValidator.validate(rawConfig);
        this.state = 'connected';
      } else {
        console.warn(`[envoy-branding] Fetch failed with status ${Number(response.status)}. Using default theme.`);
        this.config = { ...DEFAULT_ENVOY_THEME };
        this.state = 'connected';
      }
    } catch (err) {
      console.warn('[envoy-branding] Fetch failed due to network or JSON error. Using default theme.', err);
      this.config = { ...DEFAULT_ENVOY_THEME };
      this.state = 'connected';
    }

    this.notify();
  }

  private notify() {
    for (const listener of this.listeners) {
      try {
        listener(this.config, this.state);
      } catch (err) {
        console.error('[envoy-store] Listener notification failed:', err);
      }
    }
  }
}

// Export singleton instance of branding store
export const brandingStore = new BrandingStore();
