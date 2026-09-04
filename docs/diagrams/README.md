# IRIS Diagrams for Presentations

Publication-quality diagrams showing IRIS system architecture, data flow, and interactions.

## Files

1. **`iris_system_diagram.tex`** - System architecture
   - Shows: User ↔ LLM ↔ IRIS components ↔ Storage
   - Use for: High-level system overview
   - Best for: Explaining "What is IRIS?"

2. **`iris_sequence_diagram.tex`** - Interaction sequence
   - Shows: Temporal flow of a complete interaction
   - Use for: Understanding step-by-step execution
   - Best for: Explaining "How does IRIS work?"

3. **`iris_data_flow.tex`** - Data transformation flow
   - Shows: 5 phases from onboarding to learning
   - Use for: Understanding data transformations
   - Best for: Explaining "How does data flow through IRIS?"

## Compilation

### Prerequisites

**Windows (MiKTeX):**
```bash
# Install MiKTeX from miktex.org
# During compilation, MiKTeX will auto-install missing packages
```

**Linux (TeX Live):**
```bash
sudo apt-get install texlive-full
```

**macOS (MacTeX):**
```bash
brew install mactex
```

### Compile to PDF

```bash
cd docs/diagrams

# Compile individual diagram
pdflatex iris_system_diagram.tex
pdflatex iris_sequence_diagram.tex
pdflatex iris_data_flow.tex

# Output: .pdf files ready for presentation
```

### Compile to PNG (for slides)

```bash
# Install ImageMagick (if not installed)
# Windows: choco install imagemagick
# Linux: sudo apt-get install imagemagick
# macOS: brew install imagemagick

# Convert PDF to high-res PNG
magick -density 300 iris_system_diagram.pdf -quality 100 iris_system_diagram.png
magick -density 300 iris_sequence_diagram.pdf -quality 100 iris_sequence_diagram.png
magick -density 300 iris_data_flow.pdf -quality 100 iris_data_flow.png
```

### Compile All (Batch Script)

**Windows (`compile_diagrams.bat`):**
```batch
@echo off
echo Compiling IRIS diagrams...

pdflatex iris_system_diagram.tex
pdflatex iris_sequence_diagram.tex
pdflatex iris_data_flow.tex

echo Converting to PNG...
magick -density 300 iris_system_diagram.pdf -quality 100 iris_system_diagram.png
magick -density 300 iris_sequence_diagram.pdf -quality 100 iris_sequence_diagram.png
magick -density 300 iris_data_flow.pdf -quality 100 iris_data_flow.png

echo Cleaning up auxiliary files...
del *.aux *.log *.out

echo Done! Check .pdf and .png files.
```

**Linux/macOS (`compile_diagrams.sh`):**
```bash
#!/bin/bash
echo "Compiling IRIS diagrams..."

pdflatex iris_system_diagram.tex
pdflatex iris_sequence_diagram.tex
pdflatex iris_data_flow.tex

echo "Converting to PNG..."
convert -density 300 iris_system_diagram.pdf -quality 100 iris_system_diagram.png
convert -density 300 iris_sequence_diagram.pdf -quality 100 iris_sequence_diagram.png
convert -density 300 iris_data_flow.pdf -quality 100 iris_data_flow.png

echo "Cleaning up auxiliary files..."
rm -f *.aux *.log *.out

echo "Done! Check .pdf and .png files."
```

## Usage in Presentations

### PowerPoint / Keynote
- Use PNG files (high resolution, 300 DPI)
- Drag and drop into slides
- Resize as needed

### LaTeX Beamer
- Use PDF files directly
```latex
\begin{frame}{IRIS System Architecture}
    \centering
    \includegraphics[width=0.9\textwidth]{iris_system_diagram.pdf}
\end{frame}
```

### Google Slides / Web
- Upload PNG files
- Insert as images

## Customization

All diagrams use TikZ with customizable styles:

**Colors:**
```latex
user/.style={fill=blue!20}     % User actor
llm/.style={fill=green!20}     % LLM actor
iris/.style={fill=purple!20}   % IRIS components
storage/.style={fill=orange!20} % Storage
```

**Fonts:**
```latex
font=\sffamily\bfseries  % Bold sans-serif
font=\sffamily\small     % Small sans-serif
```

**Layout:**
- Adjust `node distance` for spacing
- Change `minimum width/height` for box sizes
- Modify `bend left/right` for arrow curves

## Research Citations

Diagrams include research references:

1. **GATE (Li et al., ICLR 2025)**
   - Interactive preference elicitation
   - Edge-case questions reveal tacit knowledge

2. **Wu et al. (arXiv 2406.17803)**
   - Output-driven personalization
   - Past outputs predict future preferences

3. **Westhaeusser et al. (arXiv 2510.07925)**
   - Multi-agent personalization
   - Continuous learning from implicit feedback

## Diagram Design Philosophy

**Scientific paper style:**
- Clean, professional layout
- Research citations visible
- No decorative elements
- High information density

**Presentation-ready:**
- Clear visual hierarchy
- Color-coded components
- Annotated data flows
- Self-explanatory with minimal text

## Troubleshooting

**"Package not found" errors:**
- MiKTeX: Will auto-install on first compile (accept prompts)
- TeX Live: Install full distribution or missing packages manually

**"Dimension too large" errors:**
- Reduce diagram complexity
- Split into multiple diagrams

**PNG conversion fails:**
- Check ImageMagick installation: `magick --version`
- Use alternative: `pdftoppm -png -r 300 diagram.pdf diagram`

## Version Control

**Commit:**
- `.tex` source files (yes)
- `.pdf` output files (optional, for quick reference)
- `.png` output files (no, generate as needed)
- `.aux`, `.log` files (no, LaTeX temporary files)

Add to `.gitignore`:
```
*.aux
*.log
*.out
*.synctex.gz
```
