// packages/chatbot-ui/src/branding/branding-validator.ts

import { type BrandingConfig, type OverflowMenuItemConfig } from './branding-types';
import { DEFAULT_ENVOY_THEME } from './default-theme';

export class BrandingValidator {
  /**
   * Validate raw branding configurations and merge/fix items to conform with defaults.
   */
  public static validate(raw: any): BrandingConfig {
    if (!raw || typeof raw !== 'object') {
      return { ...DEFAULT_ENVOY_THEME };
    }

    const colors = this.validateColors(raw.colors || raw.ui_theme_config || {});
    const typography = this.validateTypography(raw.typography || raw.ui_theme_config || {});
    const layout = this.validateLayout(raw.layout || raw.ui_theme_config || {});
    const assets = this.validateAssets(raw.assets || raw.ui_theme_config || {});
    const content = this.validateContent(raw.content || raw.ui_theme_config || {});
    const featureFlags = this.validateFlags(raw.featureFlags || raw.ui_theme_config || {});
    const overflowMenu = this.validateOverflowMenu(raw.overflowMenu || raw.ui_theme_config?.overflowMenu);
    const theme = (raw.theme === 'light' || raw.theme === 'dark' || raw.theme === 'auto') ? raw.theme : DEFAULT_ENVOY_THEME.theme;

    return {
      colors,
      typography,
      layout,
      assets,
      content,
      featureFlags,
      overflowMenu,
      theme
    };
  }

  private static isValidColor(color: any): boolean {
    if (typeof color !== 'string') return false;
    const clean = color.trim();
    // Validate HEX colors (e.g. #fff, #ffffff)
    const hexRegex = /^#([A-Fa-f0-9]{3}){1,2}$/;
    // Validate RGB/RGBA colors (e.g. rgb(255,255,255), rgba(0,0,0,0.5))
    const rgbRegex = /^rgba?\((\d+),\s*(\d+),\s*(\d+)(?:,\s*([\d.]+))?\)$/i;
    return hexRegex.test(clean) || rgbRegex.test(clean);
  }

  private static validateColors(colors: any): BrandingConfig['colors'] {
    const defaults = DEFAULT_ENVOY_THEME.colors;
    const validated: any = {};
    const keys = Object.keys(defaults) as Array<keyof BrandingConfig['colors']>;

    for (const key of keys) {
      const val = colors[key];
      if (this.isValidColor(val)) {
        validated[key] = val;
      } else {
        validated[key] = defaults[key];
      }
    }
    return validated;
  }

  private static validateTypography(typo: any): BrandingConfig['typography'] {
    const defaults = DEFAULT_ENVOY_THEME.typography;
    return {
      fontFamily: typeof typo.fontFamily === 'string' && typo.fontFamily.trim() ? typo.fontFamily : defaults.fontFamily,
      fontSize: typeof typo.fontSize === 'string' && typo.fontSize.trim() ? typo.fontSize : defaults.fontSize,
      headingWeight: typeof typo.headingWeight === 'number' ? typo.headingWeight : defaults.headingWeight,
      bodyWeight: typeof typo.bodyWeight === 'number' ? typo.bodyWeight : defaults.bodyWeight,
      messageTextSize: typeof typo.messageTextSize === 'string' && typo.messageTextSize.trim() ? typo.messageTextSize : defaults.messageTextSize,
      buttonTextSize: typeof typo.buttonTextSize === 'string' && typo.buttonTextSize.trim() ? typo.buttonTextSize : defaults.buttonTextSize
    };
  }

  private static validateLayout(layout: any): BrandingConfig['layout'] {
    const defaults = DEFAULT_ENVOY_THEME.layout;
    return {
      chatWidth: typeof layout.chatWidth === 'string' && layout.chatWidth.trim() ? layout.chatWidth : defaults.chatWidth,
      chatHeight: typeof layout.chatHeight === 'string' && layout.chatHeight.trim() ? layout.chatHeight : defaults.chatHeight,
      borderRadius: typeof layout.borderRadius === 'string' && layout.borderRadius.trim() ? layout.borderRadius : defaults.borderRadius,
      padding: typeof layout.padding === 'string' && layout.padding.trim() ? layout.padding : defaults.padding,
      spacing: typeof layout.spacing === 'string' && layout.spacing.trim() ? layout.spacing : defaults.spacing,
      bubbleRadius: typeof layout.bubbleRadius === 'string' && layout.bubbleRadius.trim() ? layout.bubbleRadius : defaults.bubbleRadius,
      position: this.validatePosition(layout.position || {})
    };
  }

  private static validatePosition(pos: any): BrandingConfig['layout']['position'] {
    const defaults = DEFAULT_ENVOY_THEME.layout.position || {};
    const anchor = (pos.anchor === 'bottom-right' || pos.anchor === 'bottom-left' || pos.anchor === 'top-right' || pos.anchor === 'top-left')
      ? pos.anchor
      : (defaults.anchor || 'bottom-right');
    const offsetX = typeof pos.offsetX === 'number' ? pos.offsetX : (defaults.offsetX ?? 20);
    const offsetY = typeof pos.offsetY === 'number' ? pos.offsetY : (defaults.offsetY ?? 20);

    return { anchor, offsetX, offsetY };
  }

  private static validateAssets(assets: any): BrandingConfig['assets'] {
    const defaults = DEFAULT_ENVOY_THEME.assets;
    const validated: any = {};
    const keys = Object.keys(defaults) as Array<keyof BrandingConfig['assets']>;

    for (const key of keys) {
      const val = assets[key];
      if (typeof val === 'string' && (val.startsWith('http://') || val.startsWith('https://') || val.startsWith('/') || val === '')) {
        validated[key] = val;
      } else {
        validated[key] = defaults[key];
      }
    }
    return validated;
  }

  private static validateContent(content: any): BrandingConfig['content'] {
    const defaults = DEFAULT_ENVOY_THEME.content;
    const validated: any = {};
    const keys = Object.keys(defaults) as Array<keyof BrandingConfig['content']>;

    for (const key of keys) {
      if (key === 'suggestedQuestions') {
        const val = content[key];
        if (Array.isArray(val)) {
          validated[key] = val.filter(item => typeof item === 'string');
        } else {
          validated[key] = defaults[key];
        }
        continue;
      }

      if (key === 'onlineStatus') {
        const val = content[key];
        if (typeof val === 'boolean' || val === 'online' || val === 'offline') {
          validated[key] = val;
        } else {
          validated[key] = defaults[key];
        }
        continue;
      }

      const val = content[key];
      if (typeof val === 'string' && val.trim() !== '') {
        validated[key] = val;
      } else {
        validated[key] = defaults[key];
      }
    }
    return validated;
  }

  private static validateFlags(flags: any): BrandingConfig['featureFlags'] {
    const defaults = DEFAULT_ENVOY_THEME.featureFlags;
    const validated: any = {};
    const keys = Object.keys(defaults) as Array<keyof BrandingConfig['featureFlags']>;

    for (const key of keys) {
      const val = flags[key];
      if (typeof val === 'boolean') {
        validated[key] = val;
      } else if (val === 'true' || val === 1) {
        validated[key] = true;
      } else if (val === 'false' || val === 0) {
        validated[key] = false;
      } else {
        validated[key] = defaults[key];
      }
    }
    return validated;
  }

  private static validateOverflowMenu(menu: any): OverflowMenuItemConfig[] {
    const defaults = DEFAULT_ENVOY_THEME.overflowMenu || [];
    if (!Array.isArray(menu)) return defaults;

    return menu.map((item: any) => {
      const id = typeof item.id === 'string' ? item.id : String(Math.random());
      const label = typeof item.label === 'string' ? item.label : 'Option';
      const enabled = typeof item.enabled === 'boolean' ? item.enabled : true;
      const actionType = ['restart', 'clear', 'download', 'url', 'callback'].includes(item.actionType)
        ? item.actionType
        : 'callback';
      const url = typeof item.url === 'string' ? item.url : undefined;
      const eventName = typeof item.eventName === 'string' ? item.eventName : undefined;

      return { id, label, enabled, actionType, url, eventName };
    });
  }
}
