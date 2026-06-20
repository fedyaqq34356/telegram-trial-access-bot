"use client";
import { useEffect } from "react";
import Link from "next/link";

export default function Error({ error, reset }: { error: Error & { digest?: string }; reset: () => void }) {
  useEffect(() => { console.error(error); }, [error]);
  return (
    <div className="min-h-screen grid place-items-center p-6 text-center">
      <div className="max-w-md">
        <div className="text-5xl mb-4">⚠️</div>
        <h1 className="text-2xl font-extrabold text-white mb-3">Что-то пошло не так</h1>
        <p className="text-slate-400 mb-6 text-sm">
          Произошла ошибка на этой странице. Попробуйте обновить или вернитесь на главную.
        </p>
        <div className="flex flex-col sm:flex-row gap-3 justify-center">
          <button
            onClick={reset}
            className="btn-primary justify-center"
          >
            Попробовать снова
          </button>
          <Link href="/" className="btn-ghost justify-center">
            На главную
          </Link>
        </div>
      </div>
    </div>
  );
}
