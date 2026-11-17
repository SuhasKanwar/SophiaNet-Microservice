# AI Learning Studio

Current retention behavior: [tool session state](tool_session_state.md) supersedes older page-local state notes below.


Open **Learning Studio** in the sidebar (`/chatbot/t/studio`). Its layout uses selectable format cards, a session configuration panel and a results workspace. The existing tool-heading position is preserved.

## AI actions

- **Practice quiz:** NVIDIA creates three validated multiple-choice questions and explanations. Learners answer, check their score and review explanations. Retry resets answers locally. **Generate follow-up practice** sends the original topic and missed question prompts back to NVIDIA to request a fresh quiz; it is not a validated adaptive-learning algorithm.
- **Flashcards:** NVIDIA creates five distinct question-and-answer cards through `/generate-flashcards`. Click to reveal, navigate between cards, and download Markdown. Card count, nonblank content and distinct questions are validated before display, with one model correction attempt on invalid output.
- **Narration and code scripts:** the existing CrewAI writer/editor pair produces a script through NVIDIA. Generated code is displayed only; it is never executed.

Audience and difficulty settings are included in every AI brief. The current audience choices are general learner, middle school, university student and professional; difficulty is foundational, intermediate or advanced. The settings guide generation but compliance and factual correctness still need review. The web proxy validates all supported modes and uses the configured microservice address.

Scores are computed locally from the model-generated answer key, not by a second AI call. Flipping cards, retrying the same quiz and downloads are local UI actions. All generation actions use the real model. No canned question bank or placeholder script is substituted on failure. Notes are entered as text; file upload and voice are not part of this Studio form. Results remain page-local and are replaced on generation or mode change; download to keep them.

## References and verification

Design references: [NotebookLM flashcards and quizzes](https://blog.google/innovation-and-ai/models-and-research/google-labs/notebooklm-app-quizzes-flashcards/) and [Quizlet AI study tools](https://quizlet.com/features/ai-study-tools). These informed mode selection and reveal/review interactions; they do not establish comparable learning outcomes.

47 backend tests pass, including flashcard API/schema checks, duplicate or blank card rejection and existing quiz correction. TypeScript and targeted frontend lint pass. Live API checks generated five flashcards and three quiz questions. Browser checks used a temporary signed session with the actual web proxy and NVIDIA services: quiz creation/scoring/retry, flashcard generation/reveal/navigation/download, narration and code generation, and mobile width passed. Google OAuth itself was not tested. No generated code was executed and no learning-effectiveness or factual-accuracy benchmark was run.

Python dependencies continue to use Conda `sophianet-venv`; no application dependency was added for this feature.
