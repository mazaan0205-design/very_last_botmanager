<!DOCTYPE html>
<html class="light" lang="en">

<head>
    <meta charset="utf-8" />
    <meta content="width=device-width, initial-scale=1.0" name="viewport" />
    <title>Create account — BotManager AI</title>
    <script src="https://cdn.tailwindcss.com?plugins=forms,container-queries"></script>
    <link
        href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&family=Material+Symbols+Outlined&display=swap"
        rel="stylesheet" />
    <script>
        tailwind.config = {
            darkMode: "class",
            theme: {
                extend: {
                    colors: {
                        primary: "#3525cd",
                        "primary-container": "#4f46e5",
                        "on-background": "#1b1b24",
                        "on-surface-variant": "#464555",
                        "surface": "#fcf8ff",
                        "error": "#ba1a1a",
                    },
                    borderRadius: { lg: "0.5rem", xl: "0.75rem" },
                    fontFamily: { sans: ["Inter", "sans-serif"] },
                }
            }
        }
    </script>
    <style>
        .material-symbols-outlined {
            font-variation-settings: 'FILL' 0, 'wght' 400, 'GRAD' 0, 'opsz' 24;
        }
        body { background-color: #F8FAFC; }
    </style>
</head>

<body class="font-sans text-on-background antialiased min-h-screen flex items-center justify-center px-4">

    <div class="w-full max-w-sm">

        <div class="flex flex-col items-center mb-8">
            <div class="w-11 h-11 rounded-lg bg-primary flex items-center justify-center mb-3">
                <span class="material-symbols-outlined text-white text-2xl">smart_toy</span>
            </div>
            <h1 class="text-xl font-bold text-slate-900">BotManager AI</h1>
            <p class="text-sm text-on-surface-variant mt-1">Create your account</p>
        </div>

        <div class="bg-white border border-slate-200 rounded-xl shadow-sm p-6 sm:p-8">

            @if ($errors->any())
                <div class="mb-4 px-3.5 py-2.5 rounded-lg text-sm bg-red-50 border border-red-100 text-error">
                    <ul class="list-disc list-inside space-y-0.5">
                        @foreach ($errors->all() as $error)
                            <li>{{ $error }}</li>
                        @endforeach
                    </ul>
                </div>
            @endif

            <form method="POST" action="{{ route('register.attempt') }}" class="space-y-4">
                @csrf

                <div>
                    <label for="name" class="block text-xs font-medium text-on-surface-variant mb-1.5">Full name</label>
                    <input id="name" type="text" name="name" value="{{ old('name') }}" required autofocus
                        autocomplete="name" placeholder="Ayzam Khan"
                        class="w-full rounded-lg border border-slate-200 px-3.5 py-2.5 text-sm focus:ring-2 focus:ring-primary focus:border-primary" />
                </div>

                <div>
                    <label for="email" class="block text-xs font-medium text-on-surface-variant mb-1.5">Email</label>
                    <input id="email" type="email" name="email" value="{{ old('email') }}" required
                        autocomplete="email" placeholder="you@company.com"
                        class="w-full rounded-lg border border-slate-200 px-3.5 py-2.5 text-sm focus:ring-2 focus:ring-primary focus:border-primary" />
                </div>

                <div>
                    <label for="password" class="block text-xs font-medium text-on-surface-variant mb-1.5">Password</label>
                    <input id="password" type="password" name="password" required autocomplete="new-password"
                        placeholder="At least 8 characters"
                        class="w-full rounded-lg border border-slate-200 px-3.5 py-2.5 text-sm focus:ring-2 focus:ring-primary focus:border-primary" />
                </div>

                <div>
                    <label for="password_confirmation" class="block text-xs font-medium text-on-surface-variant mb-1.5">Confirm password</label>
                    <input id="password_confirmation" type="password" name="password_confirmation" required
                        autocomplete="new-password" placeholder="••••••••"
                        class="w-full rounded-lg border border-slate-200 px-3.5 py-2.5 text-sm focus:ring-2 focus:ring-primary focus:border-primary" />
                </div>

                <button type="submit"
                    class="w-full rounded-lg py-2.5 text-sm font-semibold text-white bg-primary hover:bg-primary-container transition-colors">
                    Create account
                </button>
            </form>
        </div>

        <p class="text-center text-sm text-on-surface-variant mt-6">
            Already have an account?
            <a href="{{ route('login') }}" class="font-medium text-primary hover:underline">Sign in</a>
        </p>
    </div>

</body>
</html>
