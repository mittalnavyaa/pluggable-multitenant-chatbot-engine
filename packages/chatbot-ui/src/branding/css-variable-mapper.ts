// packages/chatbot-ui/src/branding/css-variable-mapper.ts

import { type BrandingConfig } from './branding-types';

export class CSSVariableMapper {
  /**
   * Convert BrandingConfig variables list to mapping object representing CSS Custom Properties
   */
  public static mapToCSS(config: BrandingConfig): Record<string, string> {
    const vars: Record<string, string> = {};

    // Map Colors
    if (config.colors) {
      const c = config.colors;
      if (c.primaryColor) vars['--envoy-primary'] = c.primaryColor;
      if (c.secondaryColor) vars['--envoy-secondary'] = c.secondaryColor;
      if (c.accentColor) vars['--envoy-accent'] = c.accentColor;
      if (c.backgroundColor) vars['--envoy-bg'] = c.backgroundColor;
      if (c.surfaceColor) vars['--envoy-surface'] = c.surfaceColor;
      if (c.borderColor) vars['--envoy-border'] = c.borderColor;
      if (c.textColor) vars['--envoy-text'] = c.textColor;
      if (c.mutedTextColor) vars['--envoy-muted'] = c.mutedTextColor;
      if (c.successColor) vars['--envoy-success'] = c.successColor;
      if (c.warningColor) vars['--envoy-warning'] = c.warningColor;
      if (c.errorColor) vars['--envoy-error'] = c.errorColor;

      // Dark Mode colors mapping
      if (c.darkPrimaryColor) vars['--envoy-dark-primary'] = c.darkPrimaryColor;
      if (c.darkSecondaryColor) vars['--envoy-dark-secondary'] = c.darkSecondaryColor;
      if (c.darkAccentColor) vars['--envoy-dark-accent'] = c.darkAccentColor;
      if (c.darkBackgroundColor) vars['--envoy-dark-bg'] = c.darkBackgroundColor;
      if (c.darkSurfaceColor) vars['--envoy-dark-surface'] = c.darkSurfaceColor;
      if (c.darkBorderColor) vars['--envoy-dark-border'] = c.darkBorderColor;
      if (c.darkTextColor) vars['--envoy-dark-text'] = c.darkTextColor;
      if (c.darkMutedTextColor) vars['--envoy-dark-muted'] = c.darkMutedTextColor;
    }

    // Map Typography
    if (config.typography) {
      const t = config.typography;
      if (t.fontFamily) vars['--envoy-font-family'] = t.fontFamily;
      if (t.fontSize) vars['--envoy-font-size'] = t.fontSize;
      if (t.headingWeight) vars['--envoy-heading-weight'] = String(t.headingWeight);
      if (t.bodyWeight) vars['--envoy-body-weight'] = String(t.bodyWeight);
      if (t.messageTextSize) vars['--envoy-msg-text-size'] = t.messageTextSize;
      if (t.buttonTextSize) vars['--envoy-btn-text-size'] = t.buttonTextSize;
    }

    // Map Layout
    if (config.layout) {
      const l = config.layout;
      if (l.chatWidth) vars['--envoy-chat-width'] = l.chatWidth;
      if (l.chatHeight) vars['--envoy-chat-height'] = l.chatHeight;
      if (l.borderRadius) vars['--envoy-border-radius'] = l.borderRadius;
      if (l.padding) vars['--envoy-padding'] = l.padding;
      if (l.spacing) vars['--envoy-spacing'] = l.spacing;
      if (l.bubbleRadius) vars['--envoy-bubble-radius'] = l.bubbleRadius;

      // Position offsets mapping
      if (l.position) {
        const p = l.position;
        if (p.offsetX !== undefined) vars['--envoy-offset-x'] = `${p.offsetX}px`;
        if (p.offsetY !== undefined) vars['--envoy-offset-y'] = `${p.offsetY}px`;
      }
    }

    return vars;
  }
}
