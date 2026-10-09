import type { Register } from 'claude-code';
import { atom, read, update } from 'claude-code';

const profileState = atom<'iris-profile-pane', 'profile'>('iris-profile-pane', 'profile', null);
const loadingState = atom<'iris-profile-pane', 'loading'>('iris-profile-pane', 'loading', false);
const errorState = atom<'iris-profile-pane', 'error'>('iris-profile-pane', 'error', null);

export const register: Register = (on, options) => {
  // Register slash command
  on('session.start', ($, e, next) => {
    $.command.register({
      name: 'iris-profile',
      description: 'Show IRIS profile pane'
    });
    return next(e);
  });

  // Handle command
  on('command.run', ($, e, next) => {
    if (e.command === 'iris-profile') {
      $.ui.open({
        id: 'iris-profile-pane',
        title: 'IRIS Profile'
      });
      loadProfile($);
      return { text: 'Opening IRIS profile pane...' };
    }
    return next(e);
  });

  // Render pane
  on('ui.render', ($, e, next) => {
    if (e.component === 'Pane' && e.requestId === 'iris-profile-pane') {
      return renderPane($, e);
    }
    return next(e);
  });
};

async function loadProfile($: any) {
  update($, loadingState, true);
  update($, errorState, null);

  try {
    const result = await $.tool.call({
      tool: 'mcp__iris__get_context',
      input: { query: 'profile overview' }
    });

    const text = result.content?.[0]?.text || '';

    if (text.includes('ONBOARDING_REQUIRED')) {
      update($, errorState, 'Onboarding required. Run /startIris to set up your profile.');
      update($, profileState, null);
    } else {
      // Parse profile from response
      const profile = parseProfile(text);
      update($, profileState, profile);
    }
  } catch (error) {
    update($, errorState, `Failed to load profile: ${error}`);
  } finally {
    update($, loadingState, false);
  }
}

function parseProfile(text: string): any {
  // Simple parser for profile data
  const profile = {
    language: extractField(text, 'Language:'),
    tone: extractField(text, 'Tone:'),
    format: extractField(text, 'Format Preference:'),
    boundaries: {} as Record<string, string>,
    projects: [] as string[]
  };

  // Parse boundaries
  const boundariesMatch = text.match(/### Boundaries\s+([\s\S]*?)(?=\n###|\n\n##|$)/);
  if (boundariesMatch) {
    const boundaries = boundariesMatch[1];
    const boundaryLines = boundaries.match(/- \*\*(.*?)\*\*: (.*?)(?=\n|$)/g) || [];
    boundaryLines.forEach(line => {
      const match = line.match(/\*\*(.*?)\*\*: (.*?)$/);
      if (match) {
        profile.boundaries[match[1]] = match[2];
      }
    });
  }

  // Parse projects
  const projectsMatch = text.match(/### Current Projects\s+([\s\S]*?)(?=\n###|\n\n##|$)/);
  if (projectsMatch) {
    const projects = projectsMatch[1];
    const projectLines = projects.match(/- Working on \d+ projects?: (.*?)(?=\n|$)/);
    if (projectLines) {
      profile.projects = [projectLines[1]];
    }
  }

  return profile;
}

function extractField(text: string, field: string): string {
  const match = text.match(new RegExp(`${field}\\s*\\*\\*([^*]+)\\*\\*`));
  return match ? match[1].trim() : 'N/A';
}

function renderPane($: any, e: any) {
  const { Box, Text, Button } = $.ui.resolve(e);
  const profile = read($, profileState);
  const loading = read($, loadingState);
  const error = read($, errorState);

  return (
    <Box flexDirection="column" padding={1} gap={1}>
      <Text bold color="cyan">( •‿• ) IRIS Profile</Text>

      {loading && <Text color="yellow">Loading profile...</Text>}

      {error && (
        <Box flexDirection="column" gap={1}>
          <Text color="red">{error}</Text>
          <Button
            label="Reload"
            onPress={() => loadProfile($)}
          />
        </Box>
      )}

      {profile && !loading && (
        <Box flexDirection="column" gap={1}>
          <Box flexDirection="column">
            <Text bold>Language:</Text>
            <Text>{profile.language}</Text>
          </Box>

          <Box flexDirection="column">
            <Text bold>Tone:</Text>
            <Text>{profile.tone}</Text>
          </Box>

          <Box flexDirection="column">
            <Text bold>Format:</Text>
            <Text>{profile.format}</Text>
          </Box>

          {Object.keys(profile.boundaries).length > 0 && (
            <Box flexDirection="column">
              <Text bold>Boundaries:</Text>
              {Object.entries(profile.boundaries).map(([key, value]) => (
                <Box key={key} marginLeft={2}>
                  <Text>• {key}: {value}</Text>
                </Box>
              ))}
            </Box>
          )}

          {profile.projects.length > 0 && (
            <Box flexDirection="column">
              <Text bold>Current Projects:</Text>
              {profile.projects.map((project, i) => (
                <Box key={i} marginLeft={2}>
                  <Text>• {project}</Text>
                </Box>
              ))}
            </Box>
          )}

          <Button
            label="Refresh"
            onPress={() => loadProfile($)}
          />
        </Box>
      )}
    </Box>
  );
}
