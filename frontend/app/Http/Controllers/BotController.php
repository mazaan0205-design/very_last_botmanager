<?php

namespace App\Http\Controllers;

use Illuminate\Http\Request;
use Illuminate\Support\Facades\Http;
use Illuminate\Support\Facades\Log;

class BotController extends Controller
{
    protected $apiUrl;

    public function __construct()
    {
        // Single source of truth for the FastAPI backend URL (see config/services.php).
        $this->apiUrl = rtrim(config('services.backend.url', 'http://127.0.0.1:8001'), '/');
    }

    /**
     * Resolve the owner id to scope bots by. Falls back to "default_owner"
     * only when nobody is authenticated (kept for local/dev convenience).
     */
    protected function ownerId(Request $request): string
    {
        return $request->user()
            ? (string) $request->user()->id
            : 'default_owner';
    }

    // Single, unified index method
    public function index(Request $request)
    {
        $owner = $this->ownerId($request);

        try {
            // NOTE: backend routes live under /api/bots (see backend/main.py),
            // not /bots — this was the root cause of bots never showing up.
            $response = Http::get($this->apiUrl . '/api/bots', ['owner_id' => $owner]);
            $decoded = $response->successful() ? json_decode($response->body()) : null;
            $bots = $decoded->bots ?? [];
        } catch (\Exception $e) {
            $bots = [];
        }

        $totalActiveBots = count($bots);
        $totalInteractions = 0;
        $extensionsData = [];

        if (is_array($bots)) {
            foreach ($bots as $botItem) {
                // Backend returns a flat "conversation_count" field, not a
                // nested "statistics" object.
                $totalInteractions += $botItem->conversation_count ?? 0;
            }

            // Fetch extensions for the first bot (if it exists) to use on the dashboard
            if (!empty($bots)) {
                $firstBotId = $bots[0]->id;
                $extResponse = Http::get($this->apiUrl . "/api/bots/{$firstBotId}/extensions");
                $extensionsData = $extResponse->successful() ? ($extResponse->json()['extensions'] ?? []) : [];
            }
        }

        $bot = !empty($bots) ? $bots[0] : (object) [
            'id' => 'new',
            'name' => 'No Bots Found',
            'description' => '',
            'instructions' => ''
        ];

        $apiUrl = $this->apiUrl;
        return view('dashboard', compact('bots', 'bot', 'totalActiveBots', 'totalInteractions', 'extensionsData', 'apiUrl'));
    }

    public function knowledge($id)
    {
        $response = Http::get($this->apiUrl . '/api/bots/' . $id);
        $bot = $response->successful() ? json_decode($response->body())->bot ?? null : null;
        $bot = $bot ?? (object) ['id' => $id, 'name' => 'Bot Not Found'];

        return view('knowledge-base', ['bot' => $bot, 'apiUrl' => $this->apiUrl]);
    }

    public function edit($id)
    {
        if ($id === 'new') {
            $bot = (object) ['id' => 'new', 'name' => '', 'description' => '', 'instructions' => ''];
            // New bots get the Google Workspace extension enabled by default
            // in the backend, so the toggle renders as on.
            $extensions = [];
        } else {
            $response = Http::get($this->apiUrl . '/api/bots/' . $id);
            if ($response->successful()) {
                $bot = json_decode($response->body())->bot;
            } else {
                $bot = (object) ['id' => $id, 'name' => 'Error'];
            }

            $extResponse = Http::get($this->apiUrl . '/api/bots/' . $id . '/extensions');
            $extensions = $extResponse->successful() ? ($extResponse->json()['extensions'] ?? []) : [];
        }
        return view('bot-config', ['bot' => $bot, 'extensions' => $extensions, 'apiUrl' => $this->apiUrl]);
    }

    /**
     * Handles both creating a brand new bot ($id === 'new') and updating an
     * existing one. The FastAPI backend exposes two different endpoints for
     * this (POST /api/bots to create, PUT /api/bots/{id} to update) — the
     * previous version of this method always POSTed to a Laravel-only path
     * that had no backend equivalent, which is why bot creation silently
     * failed.
     */
    public function update(Request $request, $id)
    {
        $payload = $request->all();
        $payload['owner_id'] = $payload['owner_id'] ?? $this->ownerId($request);

        if ($id === 'new') {
            $response = Http::withHeaders(['Content-Type' => 'application/json'])
                ->post($this->apiUrl . '/api/bots', $payload);
        } else {
            $response = Http::withHeaders(['Content-Type' => 'application/json'])
                ->put($this->apiUrl . '/api/bots/' . $id, $payload);
        }

        if (!$response->successful()) {
            return response()->json([
                'status' => 'error',
                'message' => $response->json('detail') ?? 'The backend rejected the request.',
            ], $response->status());
        }

        return response()->json($response->json());
    }

    public function destroy($id)
    {
        Http::delete($this->apiUrl . '/api/bots/' . $id);
        return redirect()->route('dashboard')->with('success', 'Bot successfully deleted.');
    }

    public function documentation() { return view('documentation'); }
    public function account() { return view('account'); }
    public function integrations(Request $request)
    {
        $code = $request->query('code');
        $state = $request->query('state');
        $googleError = $request->query('error');

        // Google bounced the user back with an error (e.g. access_denied)
        if ($googleError) {
            $message = $googleError === 'access_denied'
                ? 'Google connection was cancelled before it could be completed. Please try again.'
                : 'Google returned an error ('.$googleError.') and the connection was not completed.';

            return redirect()->route('integrations')->with('integration_error', $message);
        }

        // Google approved: exchange the one-time code for tokens via the backend
        if ($code) {
            $owner = $this->ownerId($request);

            // The state value we sent must come back untouched, otherwise the
            // response could bind a Google account to the wrong user.
            if (!$state || (string) $state !== (string) $owner) {
                return redirect()->route('integrations')->with(
                    'integration_error',
                    'Google sign-in could not be verified (state mismatch). Please click "Connect account" again.'
                );
            }

            try {
                // The code is only ever sent over this internal request — it is
                // never logged, stored, or echoed back to the browser.
                $response = Http::withHeaders($this->integrationHeaders($request))
                    ->timeout(20)
                    ->get($this->apiUrl.'/api/integrations/google/exchange', [
                        'code' => $code,
                        'state' => $state,
                    ]);
            } catch (\Throwable $e) {
                // Log without the exception message: Guzzle can embed the full
                // request URL, which contains the one-time code.
                Log::error('Google token exchange forward failed: backend unreachable.', ['owner' => $owner]);

                return redirect()->route('integrations')->with(
                    'integration_error',
                    'Could not reach the BotManager backend to finish the Google connection. Is uvicorn running on port 8001?'
                );
            }

            if ($response->successful()) {
                return redirect()->route('integrations')->with(
                    'integration_success',
                    'Google Workspace connected successfully. Your bot can now use Gmail, Calendar and Drive.'
                );
            }

            return redirect()->route('integrations')->with(
                'integration_error',
                $this->friendlyOAuthError($response->json('detail'))
            );
        }

        return view('integrations', ['apiUrl' => $this->apiUrl]);
    }

    /**
     * Maps backend/Google OAuth errors to safe, actionable page messages.
     * Never includes the code, client secret, or tokens.
     */
    private function friendlyOAuthError(?string $detail): string
    {
        $detail = strtolower((string) $detail);

        if (str_contains($detail, 'invalid_grant')) {
            return 'Google rejected the authorization (it may have expired or was already used). Please click "Connect account" again.';
        }
        if (str_contains($detail, 'redirect_uri_mismatch')) {
            return 'The redirect URI is not authorized in the Google app. Verify GOOGLE_REDIRECT_URI in backend/.env matches the authorized redirect URI in Google Cloud Console.';
        }
        if (str_contains($detail, 'invalid_client')) {
            return 'Google rejected the app credentials. Verify GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET in backend/.env.';
        }

        $detail = trim((string) $detail);

        return $detail !== '' ? $detail : 'Google connection could not be completed. Check the backend logs for details.';
    }

    private function integrationHeaders(Request $request): array
    {
        $owner = $this->ownerId($request);

        return [
            'X-BotManager-Owner' => 'user:' . $owner,
            'X-Runtime-Service-Token' => env('RUNTIME_SERVICE_TOKEN', 'dev-runtime-token'),
            'Accept' => 'application/json',
        ];
    }

    public function integrationStatus(Request $request)
    {
        // Proxies the backend status endpoint (/api/integrations/status) so the
        // page can render live Connected / Ready-to-connect badges.
        $response = Http::withHeaders($this->integrationHeaders($request))->get(
            $this->apiUrl.'/api/integrations/status',
            ['owner_id' => $this->ownerId($request)]
        );
        return response()->json($response->json(), $response->status());
    }

    public function connectIntegration(Request $request, string $provider)
    {
        $response = Http::withHeaders($this->integrationHeaders($request))->get(
            $this->apiUrl.'/api/integrations/'.$provider.'/connect',
            ['owner_id' => $this->ownerId($request)]
        );
        return response()->json($response->json(), $response->status());
    }

    public function disconnectIntegration(Request $request, string $provider)
    {
        $response = Http::withHeaders($this->integrationHeaders($request))->delete($this->apiUrl . '/api/integrations/' . $provider);
        return response()->json($response->json(), $response->status());
    }

    public function showPreview($id)
    {
        $response = Http::get($this->apiUrl . '/api/bots/' . $id);
        $bot = $response->successful() ? (json_decode($response->body())->bot ?? null) : null;
        $bot = $bot ?? (object) ['id' => $id];
        return view('test-preview', ['bot' => $bot, 'apiUrl' => $this->apiUrl]);
    }
}
