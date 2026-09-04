"""
Janus ASCII Art - IRIS's Butler Mascot
======================================

Two-faced JANUS representing IRIS's dual nature:
- Left face: Looks at past outputs (memory)
- Right face: Looks at current context (present)
"""


def get_janus_looking_left():
    """Butler sprite looking left (at PAST / stored memory)."""
    return """
    PAST ◀───
      ___
     /• •\\
    ( ←_• )
     \\___/
      |▓|
     /═╬═\\
    ( ▓▓▓ )
     |║║|
     | | |
    /  |  \\
    """


def get_janus_looking_right():
    """Butler sprite looking right (at PRESENT / current task)."""
    return """
       ───▶ PRESENT
        ___
       /• •\\
      ( •_→ )
       \\___/
        |▓|
       /═╬═\\
      ( ▓▓▓ )
       |║║|
       | | |
      /  |  \\
    """


def get_janus_serving():
    """Butler sprite serving (front view with tray)."""
    return """
        ___
       /• •\\
      ( •_• )
       \\___/
        |▓|
    ╔══════════╗
    ║ CONTEXT  ║
    ╚══════════╝
       /═╬═\\
      ( ▓▓▓ )
       |║║|
       | | |
      /  |  \\
    """


def get_janus_animation_frames():
    """
    Get animation frames for Janus JANUS.

    Returns list of frames for smooth animation loop:
    1. Looking left (checking PAST)
    2. Turning to center
    3. Looking right (seeing PRESENT)
    4. Turning to center
    5. Serving (holding tray)
    6. Ready pose

    Display frames sequentially to create animation effect.
    """
    return [
        # Frame 1: Looking left
        """
        JANUS JANUS
         ___
        /• •\\
       ( ←_• )
        \\___/
         |▓|
        /═╬═\\
       ( ▓▓▓ )
        |║║|
        | | |
       /  |  \\
        """,

        # Frame 2: Turning center-left
        """
        JANUS JANUS
         ___
        /• •\\
       ( ·_• )
        \\___/
         |▓|
        /═╬═\\
       ( ▓▓▓ )
        |║║|
        | | |
       /  |  \\
        """,

        # Frame 3: Center (neutral)
        """
        JANUS JANUS
         ___
        /• •\\
       ( •_• )
        \\___/
         |▓|
        /═╬═\\
       ( ▓▓▓ )
        |║║|
        | | |
       /  |  \\
        """,

        # Frame 4: Turning center-right
        """
        JANUS JANUS
         ___
        /• •\\
       ( •_· )
        \\___/
         |▓|
        /═╬═\\
       ( ▓▓▓ )
        |║║|
        | | |
       /  |  \\
        """,

        # Frame 5: Looking right
        """
        JANUS JANUS
         ___
        /• •\\
       ( •_→ )
        \\___/
         |▓|
        /═╬═\\
       ( ▓▓▓ )
        |║║|
        | | |
       /  |  \\
        """,

        # Frame 6: Back to center-right
        """
        JANUS JANUS
         ___
        /• •\\
       ( •_· )
        \\___/
         |▓|
        /═╬═\\
       ( ▓▓▓ )
        |║║|
        | | |
       /  |  \\
        """,

        # Frame 7: Center with tray appearing
        """
        JANUS JANUS
         ___
        /• •\\
       ( •_• )
        \\___/
         |▓|
       ╔═════╗
       ║     ║
       ╚═════╝
        /═╬═\\
       ( ▓▓▓ )
        |║║|
       /  |  \\
        """,

        # Frame 8: Serving (tray raised)
        """
        JANUS JANUS
         ___
        /• •\\
       ( •_• )
        \\___/
    ╔══════════╗
    ║ CONTEXT  ║
    ╚══════════╝
         |▓|
        /═╬═\\
       ( ▓▓▓ )
        |║║|
       /  |  \\
        """,
    ]


def get_janus_transition_frames():
    """
    Get compact transition animation (left -> right scan).
    Perfect for showing "searching memory -> found context" flow.
    """
    return [
        "◀─── • • •     ",
        " ◀─── • • •    ",
        "  ◀─── • • •   ",
        "   ◀─── • • •  ",
        "    ◀─── • • • ",
        "     • • • ───▶",
        "      • • • ───▶",
    ]


def get_janus_full_body():
    """Compact JANUS mascot with face expression and full body."""
    return """
           ╭─────────╮
          │  ( •_• )  │
          │  ═══════  │
           ╲   ─_─   ╱
            ╰───┬───╯
             ╱══╬══╲
            ╱   :   ╲
           │ ╱▒▒▒▒╲ │
           │ │ ◆◆◆ │ │  ← vest
           │ │ ◆◆◆ │ │
           │ ╲▒▒▒▒╱ │
         ╱─┤ ╱   ╲ ├─╲
        │  │╱     ╲│  │  ← arms
        ╰──┤       ├──╯
           │       │
          ╱ ═════ ╲
         │    :    │
         │    :    │  ← body
         │    :    │
         │    :    │
        ╱     :     ╲
       │   ╱─────╲   │
       │  │   :   │  │  ← legs
       │  │   :   │  │
      ╱   ╰─────╯   ╲
     │ ▓▓▓        ▓▓▓ │  ← shoes
     └─────┘    └─────┘

        janus JANUS
    """


def get_janus_colored():
    """Colored version of Janus for installer."""
    # ANSI colors
    CYAN = '\033[96m'
    MAGENTA = '\033[95m'
    BLUE = '\033[94m'
    YELLOW = '\033[93m'
    WHITE = '\033[97m'
    DIM = '\033[2m'
    BOLD = '\033[1m'
    RESET = '\033[0m'

    return f"""
{BOLD}{CYAN}    ╔════════════════════════════════════════════════╗{RESET}
{BOLD}{CYAN}    ║                                                ║{RESET}
{BOLD}{CYAN}    ║{RESET}       {BOLD}{WHITE}J A N U S   B U T L E R{RESET}                  {BOLD}{CYAN}║{RESET}
{BOLD}{CYAN}    ║{RESET}   {DIM}{WHITE}"Remembering past, serving present"{RESET}          {BOLD}{CYAN}║{RESET}
{BOLD}{CYAN}    ║                                                ║{RESET}
{BOLD}{CYAN}    ║{RESET}     {MAGENTA}PAST ◀───{RESET}          {BLUE}───▶ PRESENT{RESET}           {BOLD}{CYAN}║{RESET}
{BOLD}{CYAN}    ║{RESET}       {WHITE}___                ___                   {RESET}{BOLD}{CYAN}║{RESET}
{BOLD}{CYAN}    ║{RESET}      {WHITE}/• •\\              /• •\\                  {RESET}{BOLD}{CYAN}║{RESET}
{BOLD}{CYAN}    ║{RESET}     {MAGENTA}( ←_• ){RESET}            {BLUE}( •_→ ){RESET}                 {BOLD}{CYAN}║{RESET}
{BOLD}{CYAN}    ║{RESET}      {WHITE}\\___/              \\___/                  {RESET}{BOLD}{CYAN}║{RESET}
{BOLD}{CYAN}    ║{RESET}       {WHITE}|▓|                |▓|                   {RESET}{BOLD}{CYAN}║{RESET}
{BOLD}{CYAN}    ║{RESET}      {WHITE}/═╬═\\              /═╬═\\                  {RESET}{BOLD}{CYAN}║{RESET}
{BOLD}{CYAN}    ║{RESET}     {WHITE}( ▓▓▓ )            ( ▓▓▓ )                 {RESET}{BOLD}{CYAN}║{RESET}
{BOLD}{CYAN}    ║{RESET}      {WHITE}|║║|               |║║|                  {RESET}{BOLD}{CYAN}║{RESET}
{BOLD}{CYAN}    ║{RESET}      {WHITE}| | |              | | |                 {RESET}{BOLD}{CYAN}║{RESET}
{BOLD}{CYAN}    ║{RESET}     {WHITE}/  |  \\            /  |  \\                {RESET}{BOLD}{CYAN}║{RESET}
{BOLD}{CYAN}    ║                                                ║{RESET}
{BOLD}{CYAN}    ╚════════════════════════════════════════════════╝{RESET}
    """
