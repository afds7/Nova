import NextAuth from "next-auth";
import CredentialsProvider from "next-auth/providers/credentials";

const API_URL = process.env.NEXT_PUBLIC_API_URL;
const NEXTAUTH_SECRET = process.env.NEXTAUTH_SECRET || process.env.AUTH_SECRET;

const handler = NextAuth({
  providers: [
    CredentialsProvider({
      name: "credentials",
      credentials: {
        name:     { label: "Nome",  type: "text"     },
        email:    { label: "Email", type: "email"    },
        password: { label: "Senha", type: "password" },
        mode:     { label: "Mode",  type: "text"     }, // "login" | "register"
      },
      async authorize(credentials) {
        if (!credentials?.email || !credentials?.password) return null;
        if (!API_URL) {
          throw new Error('NEXT_PUBLIC_API_URL não está configurada no ambiente de produção.');
        }

        const isRegister = credentials.mode === "register";
        const endpoint = isRegister ? "/api/auth/register/" : "/api/auth/login/";

        try {
          const res = await fetch(`${API_URL}${endpoint}`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              email:    credentials.email,
              password: credentials.password,
              name:     credentials.name || "",
            }),
          });

          const data = await res.json();

          if (!res.ok) {
            // Lança o erro do backend para o NextAuth capturar e repassar ao frontend
            throw new Error(data.error || "Falha na autenticação");
          }

          // Retorna o objeto user que o NextAuth vai serializar no token JWT
          return {
            id:    data.id,
            email: data.email,
            name:  data.name,
          };
        } catch (error) {
          // Re-lança para o NextAuth tratar (vai aparecer como callbackUrl error)
          throw error;
        }
      },
    }),
  ],

  callbacks: {
    async jwt({ token, user }) {
      if (user) {
        token.id   = user.id;
        token.name = user.name;
      }
      return token;
    },

    async session({ session, token }) {
      if (session.user) {
        // @ts-ignore
        session.user.id   = token.id;
        session.user.name = token.name as string;
      }
      return session;
    },
  },

  secret: NEXTAUTH_SECRET,
  session: { strategy: "jwt" },
  pages: {
    signIn: "/",
    error:  "/",
  },
});

export { handler as GET, handler as POST };
