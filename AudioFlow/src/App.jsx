import React, { useState, useEffect } from 'react';
import Onboarding from './components/Onboarding';
import Dashboard from './components/Dashboard';
import ModeBuilder from './components/ModeBuilder';
import WatchSettings from './components/WatchSettings';
import defaultSettings from './defaultSettings.json';

// Simple Toast Component
const Toast = ({ message, onClose }) => (
  <div style={{
    position: 'fixed', bottom: '20px', right: '20px',
    backgroundColor: '#4caf50', color: 'white',
    padding: '10px 20px', borderRadius: '4px',
    boxShadow: '0 2px 10px rgba(0,0,0,0.3)',
    zIndex: 1000
  }}>
    {message}
  </div>
);

function App() {
  const [loading, setLoading] = useState(true);
  const [onboardingComplete, setOnboardingComplete] = useState(false);
  const [view, setView] = useState('dashboard');
  const [config, setConfig] = useState(null);
  const [engineStatus, setEngineStatus] = useState('stopped');
  const [jobs, setJobs] = useState({});
  const [toastMsg, setToastMsg] = useState(null);

  useEffect(() => {
    init();

    // Listen to Engine Logs/Events
    const unsubs = [
      window.electronAPI.onLog((msg) => console.log('PY:', msg)),
      window.electronAPI.onError((msg) => {
        console.error('PY ERR:', msg);
        if (msg.trim()) alert("Engine Error: " + msg);
      }),
      window.electronAPI.onExit((code) => setEngineStatus('stopped'))
    ];

    // Poll State
    const interval = setInterval(loadState, 2000);

    return () => {
      unsubs.forEach(u => u.removeListener && u.removeListener());
      clearInterval(interval);
    }
  }, []);

  useEffect(() => {
    if (toastMsg) {
      const timer = setTimeout(() => setToastMsg(null), 3000);
      return () => clearTimeout(timer);
    }
  }, [toastMsg]);

  const init = async () => {
    // Safety check for Electron API
    if (typeof window.electronAPI === 'undefined') {
      console.error("Electron API missing. Running in browser mode or preload failed.");
      setLoading(false);
      return;
    }

    try {
      const paths = await window.electronAPI.getAppPaths();

      // AUTO-SEED LOGIC:
      // 1. Check if settings.json exists (User Settings)
      // 2. If not, write defaultSettings to settings.json
      // 3. Load from settings.json

      let settingsExists = false;
      if (window.fsAPI && window.fsAPI.exists) {
        settingsExists = await window.fsAPI.exists(paths.settingsPath);
      }

      if (!settingsExists) {
        console.log("Settings file not found. Seeding from bundled defaults...");
        // Seed from bundled defaultSettings
        await window.fsAPI.writeFile(paths.settingsPath, JSON.stringify(defaultSettings, null, 2));
        console.log("Seeded settings.json from bundled defaults.");
        settingsExists = true;
      }

      if (settingsExists) {
        const cfgData = await window.fsAPI.readFile(paths.settingsPath);
        setConfig(JSON.parse(cfgData));
        setOnboardingComplete(true);
      } else {
        // Should not happen if write succeeds
        setOnboardingComplete(false);
      }
    } catch (e) {
      console.error("Init failed", e);
    } finally {
      setLoading(false);
    }
  };

  const loadState = async () => {
    if (!onboardingComplete) return;
    try {
      const paths = await window.electronAPI.getAppPaths();
      if (window.fsAPI.exists(paths.statePath)) {
        const stateData = await window.fsAPI.readFile(paths.statePath);
        const state = JSON.parse(stateData);
        setJobs(state.active_jobs || {});
      }
    } catch (e) {
      // ignore read error
    }
  };

  const startEngine = async () => {
    try {
      await window.electronAPI.startEngine('python3');
      setEngineStatus('running');
    } catch (e) {
      console.error("Start engine failed:", e);
      alert("Failed to start engine: " + e.message);
      setEngineStatus('stopped');
    }
  };

  const stopEngine = async () => {
    await window.electronAPI.stopEngine();
    setEngineStatus('stopped');
  };

  const handleCreateConfig = async (initialConfig) => {
    // User specifically requested to add default modes from config.json
    // We define the full legacy config here.

    const legacyConfig = {
      "action_definitions": {
        "transcription_podcast": {
          "id": "transcription_podcast",
          "name": "Transcription (Podcast)",
          "type": "transcription",
          "model": "gemini-1.5-flash",
          "prompt": "Generate a transcript of the episode. The episode is in Hebrew. Include timestamps and identify speakers.\nSpeakers are: \n{% for speaker in speakers %}- {{ speaker }}{% if not loop.last %}\\n{% endif %}{% endfor %}\neg:\n[00:00] Brady: Hello there.\n[00:02] Tim: Hi Brady.\nIt is important to include the correct speaker names. Use the names you identified earlier. If you really don't know the speaker's name, identify them with a letter of the alphabet, eg there may be an unknown speaker 'A' and another unknown speaker 'B'.\nIf there is music or a short jingle playing, signify like so:\n[01:02] [MUSIC] or [01:02] [JINGLE]\nIf you can identify the name of the music or jingle playing then use that instead, eg:\n[01:02] [Firework by Katy Perry] or [01:02] [The Sofa Shop jingle]\nIf there is some other sound playing try to identify the sound, eg:\n[01:02] [Bell ringing]\nEach individual caption should be quite short, a few short sentences at most.\nSignify the end of the episode with [END].\nDon't use any markdown formatting, like bolding or italics.\nOnly use characters from the Hebrew alphabet, unless you genuinely believe foreign characters are correct.\nIt is important that you use the correct words and spell everything correctly. Use the context of the podcast to help.\nIf the hosts discuss something like a movie, book or celebrity, make sure the movie, book, or celebrity name is spelled correctly."
        },
        "transcription_workshop": {
          "id": "transcription_workshop",
          "name": "Transcription (Workshop)",
          "type": "transcription",
          "model": "gemini-1.5-flash",
          "prompt": "Generate a transcript of the workshop. The audio is in Hebrew. Include timestamps and identify speakers.\nThe main speaker is HOST. Identify other speakers as SPEAKER_1, SPEAKER_2, etc.\neg:\n[00:00] HOST: Welcome everyone.\n[00:05] SPEAKER_1: I have a question.\n[00:10] HOST: Go ahead.\n\nIf there is music or a short jingle playing, signify like so:\n[01:02] [MUSIC] or [01:02] [JINGLE]\nIf you can identify the name of the music or jingle playing then use that instead, eg:\n[01:02] [Firework by Katy Perry] or [01:02] [The Sofa Shop jingle]\nIf there is some other sound playing try to identify the sound, eg:\n[01:02] [Bell ringing]\nEach individual caption should be quite short, a few short sentences at most.\nSignify the end of the episode with [END].\nDon't use any markdown formatting, like bolding or italics.\nOnly use characters from the Hebrew alphabet, unless you genuinely believe foreign characters are correct.\nIt is important that you use the correct words and spell everything correctly. Use the context to help.\n"
        },
        "summary": {
          "id": "summary",
          "name": "Summary",
          "type": "summary",
          "model": "gemini-1.5-flash",
          "prompt": "Here's the full transcript of an conversation. Please write a summary that includes the key talking points, things to remember, important notes.\nThe summary should be in Hebrew. Only use characters from the Hebrew alphabet, unless you genuinely believe foreign characters are correct.\nSince the conversation was conducted in zoom and might have included visuals, include timestamps where you deem relevant.\n"
        },
        "linkedin": {
          "id": "linkedin",
          "name": "LinkedIn Post",
          "type": "linkedin",
          "model": "gemini-1.5-flash",
          "prompt": "אתה כותב עבור פודקאסט בשם \"נקודה למחשבה\" בהנחיית עדי שמיטנקה.\nהפודקאסט פונה לאנשים רציונליים, סקרנים, בעלי צורך בהתפתחות אישית ובחשיבה עצמאית. רובם מגיעים מעולמות לוגיים או אנליטיים (כמו הייטק, מדעים, הנדסה, עיתונאות), צורכים הרבה ידע (פודקאסטים, ספרים, סרטונים) אך לא תמיד מיישמים, וחווים תחושות של עומס, בלבול או חוסר מימוש.\nהם מעריכים גישה פרקטית, שיחה בגובה העיניים, ונרתעים משיח קלישאתי או \"רוחני מדי\".\nמטרת הפודקאסט:\nלעורר נקודות מחשבה שמטלטלות בעדינות, פותחות זווית חדשה על נושאים מוכרים, ומניעות את המאזינים לשנות משהו בתפיסה או בהרגלים.\nסגנון הכתיבה הרצוי (מבוסס על הפוסטים הקיימים בלינקדאין):\nהוק חזק ומסקרן – שורה או שתיים ראשונות שגורמות לקורא לעצור. לרוב שאלה פרובוקטיבית או הצגת תופעה/פרדוקס שמחוברת לנושא הפרק.\nשפה ישירה ואותנטית – כתיבה בגובה העיניים, בלי קלישאות מוטיבציה, לפעמים עם נגיעה של הומור.\nפירוט תמציתי של הנושא – הצגת הבעיה, הרעיון המרכזי של הפרק, ודוגמאות או שאלות שהפרק עוסק בהן. לא לשקוע בפרטים מיותרים.\nפנייה אישית להאזנה – להזמין את הקורא להקשיב, לרוב עם שורה פשוטה (“קישור בתגובה הראשונה” או “להאזנה לפרק >>”).\nשמירה על אורך פוסט של כ־150–200 מילים, קריא ומזמין.\nהנחיות נוספות:\nלהשתמש במבנה של פסקאות קצרות עם שורות ריקות ביניהן, כדי שהפוסט יהיה קריא בסריקה מהירה בלינקדאין.\nלהדגיש את הייחוד של הפרק הזה ביחס לנושא – מה מפתיע, שונה או מאתגר בו.\nאפשר להוסיף אימוג’ים נקודתיים כדי לשבור טקסט, אבל לא בצורה מוגזמת (רק אם זה מרגיש טבעי).\nהמטרה היא שהקורא ירגיש שהפוסט מדבר אליו אישית ושהוא חייב ללחוץ ולהאזין.\nהמשימה שלך:\nקבל את תמליל הפרק המלא, קרא והבין את המסרים המרכזיים, ואז כתוב פוסט לינקדאין מלא לפי ההנחיות לעיל – בסגנון שתואם לפוסטים הקיימים של הפודקאסט. הפוסט צריך להציג את הרעיון המרכזי בצורה מסקרנת, להבליט את הערך שהמאזין יקבל, ולגרום לו לרצות להאזין.\nצירפתי קובץ של התמלול של הפרק שעליו נעשה את פוסט הלינדקאין.\nבנוסף צירפתי קובץ של תמלול פרק אחר שכבר עשיתי עליו פוסט לדוגמה\nוצירפתי קובץ של הפוסט שעשיתי בלינדקאין, כדי שתהיה לך דוגמה לסגנון בהתאמה לפרק."
        },
        "description": {
          "id": "description",
          "name": "Episode Description",
          "type": "description",
          "model": "gemini-1.5-flash",
          "prompt": "Here's the full transcript of an episode from my podcast 'נקודה למחשבה' – a show that sparks new ways of thinking about everyday life. The audience is mostly logical, analytical individuals, often from fields like tech, who appreciate thought-provoking content that challenges assumptions and helps them reflect on how to live more intentionally. Please write a compelling episode description that meets the following criteria:\nThe description should be in Hebrew. Only use characters from the Hebrew alphabet, unless you genuinely believe foreign characters are correct.\nOpens with a strong, curiosity-driven hook that encourages people to listen\nShort and concise (9-10 sentences max), with no fluff or repetition\nIncludes relevant keywords and themes from the episode that appeal to the target audience.\nClearly communicates what the listener will gain or think about differently after the episode\nAdd a bulleted list of key discussion points with timestamps. Base the timestamps on the questions {{ speakers_list[1] }} asks {{ speakers_list[0] }} I've attached the full transcript\nThe timestamps should in a format like \"00:00 - Intro\" - with no \"**\" for bold text, and should be in the same order as they appear in the transcript.\n"
        },
        "sales_feedback": {
          "id": "sales_feedback",
          "name": "Sales Feedback",
          "type": "sales_feedback",
          "model": "gemini-1.5-flash",
          "prompt": "אתה מאסטר במכירות, פסיכולוגיה שיווקית וניהול מו\"מ. תפקידך לנתח תמלולי שיחות מכירה בצורה חדה, ביקורתית וללא כחל וסרק.\n\nעליך לפעול לפי הכללים הבאים:\n1. שפה וטון: ענה בעברית בלבד. היה ישיר, \"אכזרי\" ומקצועי. אל תחמיא סתם ואל תתנצל על ביקורת. \n2. זיהוי דינמיקה: נתח מי הוביל את השיחה, היכן הסטטוס של המוכר ירד, ואיפה הלקוח הרגיש חוסר ביטחון או חוסר אמינות מצד המוכר.\n3. דוגמאות קונקרטיות: עבור כל טעות או נקודה לשיפור, עליך לספק חלופה מדויקת במירכאות - מה בדיוק המוכר היה צריך להגיד באותו רגע.\n4. מבנה פלט קבוע:\n   - אבחנה נוקבת: סיכום של 2-3 משפטים על למה השיחה לא נסגרה (או למה היא הייתה חלשה).\n   - טבלת ניתוח: [ציטוט מהתמלול] | [מה הבעיה (פסיכולוגית/מכירתית)] | [מה לומר במקום (ציטוט מוצע)].\n   - \"נקודת המפנה\": זיהוי הרגע המדויק שבו השיחה הוכרעה לטובה או לרעה.\n   - משימה לשיחה הבאה: פעולה אחת פרקטית ליישום מיידי.\n\nלהלן תמלול שיחת מכירה לניתוח. בצע את הניתוח בהתאם להנחיות המערכת שקיבלת, תוך התמקדות באיתור נקודות תורפה ומתן חלופות טקסטואליות בעברית."
        }
      },
      "modes": [
        {
          "id": "mode_podcast",
          "name": "Podcast",
          "trigger_keywords": ["final", "podcast"],
          "steps": [
            { "id": "step_p1", "action_def_id": "transcription_podcast" },
            { "id": "step_p2", "action_def_id": "summary", "dependency": "step_p1" },
            { "id": "step_p3", "action_def_id": "linkedin", "dependency": "step_p1" },
            { "id": "step_p4", "action_def_id": "description", "dependency": "step_p1" }
          ]
        },
        {
          "id": "mode_workshop",
          "name": "Workshop",
          "trigger_keywords": ["workshop"],
          "steps": [
            { "id": "step_w1", "action_def_id": "transcription_workshop" }
          ]
        },
        {
          "id": "mode_sales",
          "name": "Sales Feedback",
          "trigger_keywords": ["sales"],
          "steps": [
            { "id": "step_s1", "action_def_id": "transcription_workshop" },
            { "id": "step_s2", "action_def_id": "sales_feedback", "dependency": "step_s1" }
          ]
        },
        {
          "id": "mode_draft",
          "name": "Draft",
          "trigger_keywords": ["draft"],
          "steps": [
            { "id": "step_d1", "action_def_id": "transcription_podcast" }
          ]
        }
      ],
      "watched_folders": [
        "/Users/adishmitanka/Content/LongForm/נקודה למחשבה",
        "/Users/adishmitanka/Content/LongForm/Workshops"
      ]
    };

    const defaultCfg = legacyConfig;

    const paths = await window.electronAPI.getAppPaths();
    await window.fsAPI.writeFile(paths.configPath, JSON.stringify(defaultCfg, null, 2));
    setConfig(defaultCfg);
    setOnboardingComplete(true);
  };

  const handleSaveConfig = async (newConfig) => {
    const paths = await window.electronAPI.getAppPaths();
    await window.fsAPI.writeFile(paths.settingsPath, JSON.stringify(newConfig, null, 2));
    setConfig(newConfig);
    setToastMsg("Configuration Saved Successfully!");

    // Restart Engine
    if (engineStatus === 'running') {
      await stopEngine();
      setTimeout(() => startEngine(), 1000); // Simple restart delay
    }
  };

  if (loading) return <div>Loading...</div>;

  if (!onboardingComplete) {
    return <Onboarding onComplete={() => handleCreateConfig()} />;
  }

  return (
    <div style={{ display: 'flex', height: '100vh', color: 'inherit' }}>
      {/* Sidebar Nav */}
      <div style={{ width: '60px', backgroundColor: '#333', color: 'white', display: 'flex', flexDirection: 'column', alignItems: 'center', paddingTop: '20px' }}>
        <div onClick={() => setView('dashboard')} style={{ cursor: 'pointer', marginBottom: '20px', fontSize: '24px', opacity: view === 'dashboard' ? 1 : 0.5 }} title="Dashboard">📊</div>
        <div onClick={() => setView('modes')} style={{ cursor: 'pointer', marginBottom: '20px', fontSize: '24px', opacity: view === 'modes' ? 1 : 0.5 }} title="Mode Builder">⚡</div>
        <div onClick={() => setView('watch')} style={{ cursor: 'pointer', fontSize: '24px', opacity: view === 'watch' ? 1 : 0.5 }} title="Watch Folders">📂</div>
      </div>

      {/* Content */}
      <div style={{ flex: 1, backgroundColor: '#242424' }}>
        {view === 'dashboard' && (
          <Dashboard
            jobs={jobs}
            engineStatus={engineStatus}
            onToggleEngine={() => engineStatus === 'running' ? stopEngine() : startEngine()}
          />
        )}
        {view === 'modes' && (
          <ModeBuilder config={config} onSaveConfig={handleSaveConfig} />
        )}
        {view === 'watch' && (
          <WatchSettings config={config} onSaveConfig={handleSaveConfig} />
        )}
      </div>

      {toastMsg && <Toast message={toastMsg} />}
    </div>
  );
}

export default App;
