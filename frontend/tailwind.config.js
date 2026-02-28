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
                // BroCoDDE dark IDE palette
                surface: {
                    950: "#0a0907",
                    900: "#0f0e0b",
                    800: "#1a1814",
                    700: "#252219",
                    600: "#302d22",
                },
                border: {
                    subtle: "#2a2620",
                    default: "#3d3828",
                    emphasis: "#524d3a",
                },
                gold: {
                    300: "#e8c97d",
                    400: "#d4a843",
                    500: "#b8902f",
                    600: "#9a7520",
                },
                text: {
                    primary: "#f0ead8",
                    secondary: "#a89d7e",
                    muted: "#6b6252",
                    inverse: "#0a0907",
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
                "2xs": ["0.65rem", { lineHeight: "1rem" }],
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
