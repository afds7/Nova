type NovaLogoProps = {
  className?: string;
};

/** Mantém o recorte da arte estável para que a logo não encolha nem seja cortada no mobile. */
export default function NovaLogo({ className = '' }: NovaLogoProps) {
  return (
    <div className={`relative h-24 w-56 shrink-0 overflow-hidden ${className}`}>
      <img
        src="/logo-nova.png"
        alt="Logo NOVA Hub"
        width={650}
        height={366}
        className="absolute left-[-184px] top-[-121px] h-auto w-[540px] max-w-none sm:left-[-220px] sm:top-[-145px] sm:w-[650px]"
      />
    </div>
  );
}
