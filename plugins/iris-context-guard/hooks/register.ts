import type { Register } from 'claude-code';
import { atom, read, update } from 'claude-code';

const contextLoadedAtom = atom<'iris-context-guard', 'contextLoadedThisTurn'>('iris-context-guard', 'contextLoadedThisTurn', false);

export const register: Register = (on, options) => {
  // Reset flag at turn start
  on('turn.start', ($, e, next) => {
    update($, contextLoadedAtom, false);
    return next(e);
  });

  // Track get_context calls
  on('tool.call', ($, e, next) => {
    if (e.tool === 'mcp__iris__get_context') {
      update($, contextLoadedAtom, true);
    }
    return next(e);
  });

  // Validate at turn end
  on('turn.end', ($, e, next) => {
    const contextLoaded = read($, contextLoadedAtom);

    if (!contextLoaded && !e.error) {
      // Only warn if the turn succeeded (no error)
      // and if there was actual user input (not just a notification)
      if (e.messages?.some((m: any) => m.role === 'user' && m.content?.length > 0)) {
        $.ui.toast('⚠️ IRIS context not loaded — response may not be personalized');
      }
    }

    return next(e);
  });
};
