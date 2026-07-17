// packages/chatbot-ui/src/branding/branding-types.ts

export interface BrandingThemeColors {
  primaryColor?: string;
  secondaryColor?: string;
  accentColor?: string;
  backgroundColor?: string;
  surfaceColor?: string;
  borderColor?: string;
  textColor?: string;
  mutedTextColor?: string;
  successColor?: string;
  warningColor?: string;
  errorColor?: string;

  // Dark mode overrides
  darkPrimaryColor?: string;
  darkSecondaryColor?: string;
  darkAccentColor?: string;
  darkBackgroundColor?: string;
  darkSurfaceColor?: string;
  darkBorderColor?: string;
  darkTextColor?: string;
  darkMutedTextColor?: string;
}

export interface BrandingTypography {
  fontFamily?: string;
  fontSize?: string;
  headingWeight?: number;
  bodyWeight?: number;
  messageTextSize?: string;
  buttonTextSize?: string;
}

export interface WidgetPositionConfig {
  anchor?: 'bottom-right' | 'bottom-left' | 'top-right' | 'top-left';
  offsetX?: number;
  offsetY?: number;
}

export interface BrandingLayout {
  chatWidth?: string;
  chatHeight?: string;
  borderRadius?: string;
  padding?: string;
  spacing?: string;
  bubbleRadius?: string;
  position?: WidgetPositionConfig;
}

export interface BrandingAssets {
  companyLogo?: string;
  chatAvatar?: string;
  botAvatar?: string;
  launcherIcon?: string;
  headerIcon?: string;
}

export interface BrandingContent {
  widgetTitle?: string;
  welcomeMessage?: string;
  placeholderText?: string;
  offlineMessage?: string;
  errorMessage?: string;
  typingIndicatorText?: string;
  subtitle?: string;
  onlineStatus?: boolean | 'online' | 'offline';
  suggestedQuestions?: string[];
}

export interface BrandingFeatureFlags {
  fileUpload?: boolean;
  voiceInput?: boolean;
  suggestedQuestions?: boolean;
  typingAnimation?: boolean;
  streamingResponses?: boolean;
  conversationHistory?: boolean;
}

export interface OverflowMenuItemConfig {
  id: string;
  label: string;
  enabled?: boolean;
  actionType: 'restart' | 'clear' | 'download' | 'url' | 'callback';
  url?: string;
  eventName?: string;
}

export interface BrandingConfig {
  colors: BrandingThemeColors;
  typography: BrandingTypography;
  layout: BrandingLayout;
  assets: BrandingAssets;
  content: BrandingContent;
  featureFlags: BrandingFeatureFlags;
  overflowMenu?: OverflowMenuItemConfig[];
  theme?: 'light' | 'dark' | 'auto';
}
