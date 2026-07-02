<?php

namespace App\Http\Controllers;

use Illuminate\Http\Request;
use Illuminate\Support\Facades\Http;

class BotController extends Controller
{
    protected $apiUrl;

    public function __construct()
    {
        $this->apiUrl = env('PYTHON_API_URL', 'http://127.0.0.1:8001');
    }

    // Single, unified index method
    public function index()
    {
        try {
            $response = Http::get($this->apiUrl . '/bots/list');
            $bots = $response->successful() ? json_decode($response->body()) : [];
        } catch (\Exception $e) {
            $bots = [];
        }

        $totalActiveBots = count($bots);
        $totalInteractions = 0;
        $extensionsData = [];

        if (is_array($bots)) {
            foreach ($bots as $botItem) {
                $totalInteractions += $botItem->statistics->conversations ?? 0;
            }

            // Fetch extensions for the first bot (if it exists) to use on the dashboard
            if (!empty($bots)) {
                $firstBotId = $bots[0]->id;
                $extResponse = Http::get($this->apiUrl . "/bots/{$firstBotId}/extensions");
                $extensionsData = $extResponse->successful() ? $extResponse->json() : [];
            }
        }

        $bot = !empty($bots) ? $bots[0] : (object) [
            'id' => 'new',
            'name' => 'No Bots Found',
            'description' => '',
            'instructions' => ''
        ];

        return view('dashboard', compact('bots', 'bot', 'totalActiveBots', 'totalInteractions', 'extensionsData'));
    }

    public function knowledge($id)
    {
        $response = Http::get($this->apiUrl . '/bots/' . $id);
        $bot = $response->successful() ? json_decode($response->body()) : (object) ['id' => $id, 'name' => 'Bot Not Found'];

        return view('knowledge-base', compact('bot'));
    }

    public function edit($id)
    {
        if ($id === 'new') {
            $bot = (object) ['id' => 'new', 'name' => '', 'description' => '', 'instructions' => ''];
        } else {
            $response = Http::get($this->apiUrl . '/bots/' . $id);
            $bot = $response->successful() ? json_decode($response->body()) : (object) ['id' => $id, 'name' => 'Error'];
        }
        return view('bot-config', compact('bot'));
    }

    public function update(Request $request, $id)
    {
        $response = Http::withHeaders(['Content-Type' => 'application/json'])
                        ->post($this->apiUrl . '/bots/update/' . $id, $request->all());
        return response()->json($response->json());
    }

    public function destroy($id)
    {
        Http::delete($this->apiUrl . '/bots/' . $id);
        return redirect()->route('dashboard')->with('success', 'Bot successfully deleted.');
    }

    public function documentation() { return view('documentation'); }
    public function account() { return view('account'); }

    public function showPreview($id)
    {
        $response = Http::get($this->apiUrl . '/bots/' . $id);
        $bot = $response->successful() ? json_decode($response->body()) : (object)['id' => $id];
        return view('test-preview', compact('bot'));
    }

    public function showExtensions($id)
    {
        $response = Http::get($this->apiUrl . '/bots/' . $id);
        $bot = $response->successful() ? json_decode($response->body()) : (object)['id' => $id, 'name' => 'Bot'];

        $extResponse = Http::get($this->apiUrl . '/bots/' . $id . '/extensions');
        $extensionsData = $extResponse->successful() ? $extResponse->json() : [];

        return view('bots.extensions', compact('bot', 'extensionsData'));
    }

    public function toggleExtension(Request $request, $bot_id, $extension_id)
{
    // 1. Get current list from the backend/database
    $tools = $this->backendService->get_enabled_tools($bot_id);

    // 2. Logic: Add or remove the tool ID
    if ($request->status) {
        if (!in_array($extension_id, $tools)) {
            $tools[] = $extension_id;
        }
    } else {
        $tools = array_diff($tools, [$extension_id]);
    }

    // 3. Save the updated array back via the backend service
    $this->backendService->save_enabled_tools($bot_id, array_values($tools));

    return response()->json(['success' => true]);
}
}
