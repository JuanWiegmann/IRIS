import type { Register } from 'claude-code';

export const register: Register = (on, options) => {
  // Update status on session start
  on('session.start', async ($, e, next) => {
    await updateIrisStatus($);
    return next(e);
  });

  // Update status after each turn
  on('turn.end', async ($, e, next) => {
    await updateIrisStatus($);
    return next(e);
  });
};

async function updateIrisStatus($: any) {
  try {
    // Call IRIS get_context to check status
    const result = await $.tool.call({
      tool: 'mcp__iris__get_context',
      input: { query: 'status check' }
    });

    if (result.content?.[0]?.text?.includes('ONBOARDING_REQUIRED')) {
      $.ui.status('⚠️ IRIS: onboarding required');
    } else {
      $.ui.status('( •‿• ) IRIS');
    }
  } catch (error) {
    // IRIS not available or error
    $.ui.status('IRIS: not connected');
  }
}
