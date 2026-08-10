<?php

namespace App\Http\Controllers;

use Illuminate\Http\Request;
use Illuminate\Support\Facades\Http;

class BotController extends Controller
{
    protected $apiUrl;

    public function __construct()
    {
        $this->apiUrl = rtrim(env('PYTHON_API_URL', 'http://127.0.0.1:8001'), '/');
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

        return view('knowledge-base', compact('bot'));
    }

    public function edit($id)
    {
        if ($id === 'new') {
            $bot = (object) ['id' => 'new', 'name' => '', 'description' => '', 'instructions' => ''];
        } else {
            $response = Http::get($this->apiUrl . '/api/bots/' . $id);
            if ($response->successful()) {
                $bot = json_decode($response->body())->bot;
            } else {
                $bot = (object) ['id' => $id, 'name' => 'Error'];
            }
        }
        return view('bot-config', compact('bot'));
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
    public function integrations() { return view('integrations', ['apiUrl' => $this->apiUrl]); }

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
        // NOTE: the backend does not currently expose a generic /integrations
        // status/connect/disconnect endpoint (see backend/integrations.py,
        // which only defines /api/integrations/gmail/*, /calendar/events,
        // and /drive/search). These three methods will keep returning
        // errors until that surface is built out on the backend — flagged
        // separately, not fixed as part of the bot-creation bug.
        $response = Http::withHeaders($this->integrationHeaders($request))->get($this->apiUrl . '/api/integrations');
        return response()->json($response->json(), $response->status());
    }

    public function connectIntegration(Request $request, string $provider)
    {
        $response = Http::withHeaders($this->integrationHeaders($request))->get($this->apiUrl . '/api/integrations/' . $provider . '/connect');
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
        return view('test-preview', compact('bot'));
    }
}
