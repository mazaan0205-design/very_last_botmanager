<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\DB;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    public function up(): void
    {
        Schema::create('organizations', function (Blueprint $table) {
            $table->id();
            $table->string('name');
            $table->string('slug')->unique();
            $table->timestamps();
        });

        Schema::create('organization_user', function (Blueprint $table) {
            $table->id();
            $table->foreignId('organization_id')->constrained()->cascadeOnDelete();
            $table->foreignId('user_id')->constrained()->cascadeOnDelete();
            $table->string('role')->default('builder');
            $table->timestamps();
            $table->unique(['organization_id', 'user_id']);
        });

        Schema::table('users', function (Blueprint $table) {
            $table->foreignId('current_organization_id')->nullable()->after('password')->constrained('organizations')->nullOnDelete();
        });

        Schema::create('agents', function (Blueprint $table) {
            $table->uuid('id')->primary();
            $table->foreignId('organization_id')->constrained()->cascadeOnDelete();
            $table->string('mode')->default('chatbot');
            $table->string('name');
            $table->text('description')->nullable();
            $table->longText('instructions');
            $table->string('engine')->default('llama-3.3-70b-versatile');
            $table->string('provider')->default('groq');
            $table->decimal('temperature', 3, 2)->default(0.3);
            $table->boolean('guardrails')->default(true);
            $table->string('public_slug')->nullable()->unique();
            $table->json('embed_allowed_origins')->nullable();
            $table->unsignedBigInteger('conversations_count')->default(0);
            $table->timestamps();
            $table->index(['organization_id', 'mode']);
        });

        Schema::create('agent_knowledge_sources', function (Blueprint $table) {
            $table->id();
            $table->uuid('agent_id');
            $table->foreign('agent_id')->references('id')->on('agents')->cascadeOnDelete();
            $table->string('file_name');
            $table->string('source_type')->default('txt');
            $table->string('status')->default('pending');
            $table->timestamps();
        });

        Schema::create('agent_chunks', function (Blueprint $table) {
            $table->id();
            $table->uuid('agent_id');
            $table->foreign('agent_id')->references('id')->on('agents')->cascadeOnDelete();
            $table->foreignId('agent_knowledge_source_id')->nullable()->constrained()->nullOnDelete();
            $table->longText('content');
            $table->json('embedding')->nullable();
            $table->timestamps();
        });

        Schema::create('agent_extensions', function (Blueprint $table) {
            $table->uuid('agent_id')->primary();
            $table->foreign('agent_id')->references('id')->on('agents')->cascadeOnDelete();
            $table->json('enabled_tools')->nullable();
        });

        Schema::create('embed_tokens', function (Blueprint $table) {
            $table->id();
            $table->uuid('agent_id');
            $table->foreign('agent_id')->references('id')->on('agents')->cascadeOnDelete();
            $table->string('token', 64)->unique();
            $table->json('allowed_origins')->nullable();
            $table->boolean('is_active')->default(true);
            $table->timestamps();
        });

        Schema::create('api_keys', function (Blueprint $table) {
            $table->id();
            $table->foreignId('organization_id')->constrained()->cascadeOnDelete();
            $table->string('name');
            $table->string('key_prefix', 12);
            $table->string('key_hash', 64);
            $table->json('scopes')->nullable();
            $table->timestamp('last_used_at')->nullable();
            $table->timestamps();
        });

        Schema::create('conversations', function (Blueprint $table) {
            $table->uuid('id')->primary();
            $table->uuid('agent_id');
            $table->foreign('agent_id')->references('id')->on('agents')->cascadeOnDelete();
            $table->string('title')->nullable();
            $table->string('channel')->default('playground');
            $table->timestamps();
        });

        Schema::create('messages', function (Blueprint $table) {
            $table->id();
            $table->uuid('conversation_id');
            $table->foreign('conversation_id')->references('id')->on('conversations')->cascadeOnDelete();
            $table->string('role');
            $table->longText('content')->nullable();
            $table->json('tool_calls')->nullable();
            $table->json('metadata')->nullable();
            $table->timestamps();
        });

        Schema::create('integration_catalog', function (Blueprint $table) {
            $table->id();
            $table->string('key')->unique();
            $table->string('name');
            $table->json('oauth_scopes')->nullable();
            $table->boolean('is_active')->default(true);
        });

        Schema::create('org_integrations', function (Blueprint $table) {
            $table->id();
            $table->foreignId('organization_id')->constrained()->cascadeOnDelete();
            $table->string('provider');
            $table->text('credentials_encrypted');
            $table->json('scopes')->nullable();
            $table->string('status')->default('connected');
            $table->timestamps();
            $table->unique(['organization_id', 'provider']);
        });

        Schema::create('mcp_servers', function (Blueprint $table) {
            $table->id();
            $table->foreignId('organization_id')->constrained()->cascadeOnDelete();
            $table->string('name');
            $table->string('transport')->default('stdio');
            $table->json('config');
            $table->string('health_status')->default('unknown');
            $table->timestamps();
        });

        Schema::create('agent_tools', function (Blueprint $table) {
            $table->id();
            $table->uuid('agent_id');
            $table->foreign('agent_id')->references('id')->on('agents')->cascadeOnDelete();
            $table->string('source_type');
            $table->string('source_id')->nullable();
            $table->string('tool_name');
            $table->boolean('is_enabled')->default(true);
            $table->timestamps();
        });

        Schema::create('agent_runs', function (Blueprint $table) {
            $table->uuid('id')->primary();
            $table->uuid('agent_id');
            $table->foreign('agent_id')->references('id')->on('agents')->cascadeOnDelete();
            $table->uuid('conversation_id')->nullable();
            $table->foreign('conversation_id')->references('id')->on('conversations')->nullOnDelete();
            $table->string('status')->default('pending');
            $table->json('plan')->nullable();
            $table->json('steps')->nullable();
            $table->text('error')->nullable();
            $table->timestamps();
        });

        Schema::create('usage_events', function (Blueprint $table) {
            $table->id();
            $table->foreignId('organization_id')->constrained()->cascadeOnDelete();
            $table->uuid('agent_id')->nullable();
            $table->string('event_type');
            $table->unsignedInteger('units')->default(1);
            $table->json('metadata')->nullable();
            $table->timestamps();
        });

        Schema::create('agent_schedules', function (Blueprint $table) {
            $table->id();
            $table->uuid('agent_id');
            $table->foreign('agent_id')->references('id')->on('agents')->cascadeOnDelete();
            $table->string('cron_expression');
            $table->longText('prompt');
            $table->boolean('is_active')->default(true);
            $table->timestamp('last_run_at')->nullable();
            $table->timestamps();
        });

        Schema::create('webhook_endpoints', function (Blueprint $table) {
            $table->id();
            $table->foreignId('organization_id')->constrained()->cascadeOnDelete();
            $table->uuid('agent_id')->nullable();
            $table->foreign('agent_id')->references('id')->on('agents')->nullOnDelete();
            $table->string('url');
            $table->string('secret');
            $table->json('events')->nullable();
            $table->boolean('is_active')->default(true);
            $table->timestamps();
        });

        Schema::create('agent_templates', function (Blueprint $table) {
            $table->id();
            $table->string('name');
            $table->string('mode');
            $table->longText('instructions');
            $table->json('default_tools')->nullable();
            $table->boolean('is_public')->default(true);
            $table->timestamps();
        });

        if (DB::getDriverName() === 'pgsql') {
            DB::statement('CREATE EXTENSION IF NOT EXISTS vector');
            Schema::table('agent_chunks', function (Blueprint $table) {
                $table->dropColumn('embedding');
            });
            DB::statement('ALTER TABLE agent_chunks ADD COLUMN embedding vector(1536)');
        }

        DB::table('integration_catalog')->insert([
            ['key' => 'google', 'name' => 'Google (Gmail & Calendar)', 'oauth_scopes' => json_encode(['gmail.readonly', 'calendar.events']), 'is_active' => true, 'created_at' => now(), 'updated_at' => now()],
            ['key' => 'slack', 'name' => 'Slack', 'oauth_scopes' => json_encode(['channels:read', 'chat:write']), 'is_active' => true, 'created_at' => now(), 'updated_at' => now()],
        ]);

        DB::table('agent_templates')->insert([
            ['name' => 'Website Support Chatbot', 'mode' => 'chatbot', 'instructions' => 'You are a helpful customer support assistant. Answer from the knowledge base when possible.', 'default_tools' => json_encode(['instant_faq']), 'is_public' => true, 'created_at' => now(), 'updated_at' => now()],
            ['name' => 'Operations Agent', 'mode' => 'agent', 'instructions' => 'You are an operations agent. Break tasks into steps, use connected tools, and report outcomes clearly.', 'default_tools' => json_encode([]), 'is_public' => true, 'created_at' => now(), 'updated_at' => now()],
        ]);
    }

    public function down(): void
    {
        Schema::dropIfExists('agent_templates');
        Schema::dropIfExists('webhook_endpoints');
        Schema::dropIfExists('agent_schedules');
        Schema::dropIfExists('usage_events');
        Schema::dropIfExists('agent_runs');
        Schema::dropIfExists('agent_tools');
        Schema::dropIfExists('mcp_servers');
        Schema::dropIfExists('org_integrations');
        Schema::dropIfExists('integration_catalog');
        Schema::dropIfExists('messages');
        Schema::dropIfExists('conversations');
        Schema::dropIfExists('api_keys');
        Schema::dropIfExists('embed_tokens');
        Schema::dropIfExists('agent_extensions');
        Schema::dropIfExists('agent_chunks');
        Schema::dropIfExists('agent_knowledge_sources');
        Schema::dropIfExists('agents');
        Schema::table('users', function (Blueprint $table) {
            $table->dropConstrainedForeignId('current_organization_id');
        });
        Schema::dropIfExists('organization_user');
        Schema::dropIfExists('organizations');
    }
};
