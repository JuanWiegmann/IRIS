interface PluginState {
  'iris-profile-pane': {
    profile: {
      language: string;
      tone: string;
      format: string;
      boundaries: Record<string, string>;
      projects: string[];
    } | null;
    loading: boolean;
    error: string | null;
  };
}
