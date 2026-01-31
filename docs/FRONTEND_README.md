# ResumeAI - Next.js Frontend

Modern Next.js 14 frontend for the Recruiter-Pro-AI system with 4-agent ML pipeline.

## 🚀 Features

- **Next.js 14** with App Router
- **TypeScript** for type safety
- **Tailwind CSS** with custom navy theme
- **React Dropzone** for file uploads
- **Axios** for API communication
- **Lucide React** for icons
- **Sonner** for toast notifications

## 📦 Installation

```bash
npm install
```

## 🔧 Configuration

Create `.env.local`:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## 🏃 Running

### Development Mode

```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000)

### Production Build

```bash
npm run build
npm start
```

## 📁 Project Structure

```
frontend/
├── app/                  # Next.js App Router pages
│   ├── page.tsx         # Dashboard
│   ├── upload/          # Upload CVs
│   ├── results/         # Match history
│   ├── jobs/            # Job database
│   ├── layout.tsx       # Root layout
│   └── globals.css      # Global styles
├── components/
│   ├── layout/          # Sidebar, Header
│   └── upload/          # MatchCard, MatchSummary
├── lib/
│   ├── api.ts          # API client
│   ├── types.ts        # TypeScript types
│   └── utils.ts        # Utility functions
└── public/             # Static assets
```

## 🎨 Design System

- **Background**: Navy-900 (#0f1729)
- **Cards**: Navy-800 (#1a2332)
- **Accent**: Blue-500
- **Borders**: White/10 opacity with glassmorphism

## 🔌 API Integration

Backend must be running on port 8000:

```bash
# From project root
.\Run.ps1
```

### API Endpoints

- `GET /health` - Health check
- `GET /jobs` - List jobs (limit, skip, search)
- `POST /match` - Match CV to jobs
- `POST /match/single` - Match CV to single job
- `GET /match/history` - Get match history

## 📄 Pages

### Dashboard (`/`)
- Welcome hero section
- 3 feature cards (Upload, Results, Jobs)
- System architecture overview
- 4-agent pipeline explanation

### Upload CVs (`/upload`)
- Drag & drop file uploader
- Batch matching (multiple CVs)
- Real-time processing status
- Match results with summary cards

### Results (`/results`)
- Match history with filters
- Sort by date or score
- Expandable match cards
- Summary statistics

### Job Database (`/jobs`)
- Search all 3,000 jobs
- Grid layout with expandable cards
- Company, location, job type filters
- Pagination (12 per page)

## 🧩 Components

### MatchCard
- Color-coded borders (green/yellow/orange)
- Agent scores breakdown
- Expandable AI explanation
- Job details

### MatchSummary
- High/medium/low match counts
- Average score calculation
- Visual statistics cards

### Sidebar
- Fixed navigation
- Live API status indicator
- Active state highlighting

## 📊 Features

- **Real-time API Status**: Live health check every 10s
- **File Upload**: PDF, DOCX, TXT support
- **Match Scoring**: Color-coded by confidence
- **History Tracking**: All matches saved
- **Responsive Design**: Mobile-friendly layout

## 🔨 Development

```bash
# Install dependencies
npm install

# Run dev server
npm run dev

# Type check
npm run type-check

# Build for production
npm run build

# Start production server
npm start
```

## 🌐 Environment Variables

- `NEXT_PUBLIC_API_URL` - FastAPI backend URL (default: http://localhost:8000)

## 📝 License

MIT
