import { AuthForm } from "@/components/auth/auth-form";

export const metadata = { title: "Sign In" };

export default function LoginPage() {
  return <AuthForm mode="login" />;
}
