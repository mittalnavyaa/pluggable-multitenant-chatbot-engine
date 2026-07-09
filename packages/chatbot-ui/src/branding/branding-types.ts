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
}

export interface BrandingTypography {
  fontFamily?: string;
  fontSize?: string;
  headingWeight?: number;
  bodyWeight?: number;
  messageTextSize?: string;
  buttonTextSize?: string;
}

export interface BrandingLayout {
  chatWidth?: string;
  chatHeight?: string;
  borderRadius?: string;
  padding?: string;
  spacing?: string;
  bubbleRadius?: string;
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
}

export interface BrandingFeatureFlags {
  fileUpload?: boolean;
  voiceInput?: boolean;
  suggestedQuestions?: boolean;
  typingAnimation?: boolean;
  streamingResponses?: boolean;
  conversationHistory?: boolean;
}

export interface BrandingConfig {
  colors: BrandingThemeColors;
  typography: BrandingTypography;
  layout: BrandingLayout;
  assets: BrandingAssets;
  content: BrandingContent;
  featureFlags: BrandingFeatureFlags;
}
