"""
A collection of svg icons
"""

PLAY_ICON: str = """
<svg viewBox="0 0 128 128" xmlns="http://www.w3.org/2000/svg" 
     style="width: 1em; height: 1em; display: inline-block; vertical-align: middle;">
  <g transform="translate(52,20) rotate(8)">
    <rect x="0" y="0" width="56" height="80" rx="10" fill="#ffffff" stroke="#000000" stroke-width="3"/>
  </g>
  <g transform="translate(28,32) rotate(-4)">
    <rect x="0" y="0" width="56" height="80" rx="10" fill="#ffffff" stroke="#000000" stroke-width="3"/>
    <polygon points="22,26 22,54 42,40" fill="#000000"/>
  </g>
</svg>
"""


TAB_ICON: str = """
<svg width="128" height="128" viewBox="0 0 128 128" xmlns="http://www.w3.org/2000/svg">
  <!-- Back card -->
  <g transform="translate(56,18) rotate(8)">
    <rect x="0" y="0" width="52" height="72" rx="8"
          fill="#ffffff"
          stroke="#1f2a44"
          stroke-width="3"/>
  </g>

  <!-- Front card -->
  <g transform="translate(20,30) rotate(-4)">
    <rect x="0" y="0" width="64" height="88" rx="10"
          fill="#ffffff"
          stroke="#ff3b30"
          stroke-width="5"/>

    <!-- Bold % symbol (optimized for visibility) -->
    <text x="32" y="58"
          font-size="48"
          font-family="Arial, Helvetica, sans-serif"
          font-weight="900"
          text-anchor="middle"
          dominant-baseline="middle"
          fill="#ff3b30">
      %
    </text>
  </g>
</svg>
"""

TAB_ICON2: str = """
<svg width="128" height="128" viewBox="0 0 128 128" xmlns="http://www.w3.org/2000/svg">
  <!-- Back card 1 -->
  <g transform="translate(56,16) rotate(10)">
    <rect x="0" y="0" width="56" height="80" rx="10"
          fill="#ffffff"
          stroke="#000000"
          stroke-width="3"/>
  </g>

  <!-- Back card 2 -->
  <g transform="translate(40,24) rotate(5)">
    <rect x="0" y="0" width="56" height="80" rx="10"
          fill="#ffffff"
          stroke="#000000"
          stroke-width="3"/>
  </g>

  <!-- Front card -->
  <g transform="translate(24,32) rotate(-4)">
    <rect x="0" y="0" width="56" height="80" rx="10"
          fill="#ffffff"
          stroke="#000000"
          stroke-width="3"/>

    <!-- Centered % symbol -->
    <text x="28" y="40"
          font-size="44"
          font-family="Arial, Helvetica, sans-serif"
          font-weight="900"
          text-anchor="middle"
          dominant-baseline="middle"
          fill="#000000">
      %
    </text>
  </g>
</svg>
"""
