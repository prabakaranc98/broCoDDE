/** @type {import('tailwindcss').Config} */
module.exports = {
    content: [
        "./app/**/*.{ts,tsx}",
        "./components/**/*.{ts,tsx}",
        "./lib/**/*.{ts,tsx}",
    ],
    theme: {
        extend: {
            colors: {
                // BroCoDDE monochrome palette
                surface: {
                    950: "#080808",
                    900: "#101010",
                    800: "#181818",
                    700: "#212121",
                    600: "#2a2a2a",
                },
                border: {
                    subtle: "#262626",
                    default: "#3a3a3a",
                    emphasis: "#525252",
                },
                gold: {
                    300: "#ebebeb",
                    400: "#d8d8d8",
                    500: "#b8b8b8",
                    600: "#909090",
                },
                text: {
                    primary: "#f5f5f5",
                    secondary: "#c0c0c0",
                    muted: "#787878",
                    inverse: "#080808",
                },
                stage: {
                    discovery: "#4f7ec8",
                    extraction: "#7c5cbf",
                    structuring: "#2d9e8a",
                    drafting: "#e8a838",
                    vetting: "#d4704a",
                    ready: "#4aad6f",
                    "post-mortem": "#8a7a6a",
                },
                lint: {
                    pass: "#4aad6f",
                    fail: "#d4704a",
                },
            },
            fontFamily: {
                sans: ["DM Sans", "system-ui", "sans-serif"],
                mono: ["JetBrains Mono", "Fira Code", "monospace"],
            },
            fontSize: {
                "2xs": ["0.72rem", { lineHeight: "1.1rem" }],
            },
            animation: {
                "pulse-slow": "pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite",
                "fade-in": "fadeIn 0.2s ease-out",
                "slide-up": "slideUp 0.25s ease-out",
            },
            keyframes: {
                fadeIn: { from: { opacity: "0" }, to: { opacity: "1" } },
                slideUp: {
                    from: { opacity: "0", transform: "translateY(6px)" },
                    to: { opacity: "1", transform: "translateY(0)" },
                },
            },
        },
    },
    plugins: [],
};
