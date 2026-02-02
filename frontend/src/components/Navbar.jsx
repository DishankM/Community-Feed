function Navbar() {
  return (
    <nav className="bg-white shadow-sm sticky top-0 z-50">
      <div className="container mx-auto px-4 py-4">
        <div className="flex items-center justify-between">
          <h1 className="text-2xl font-bold text-gray-800">
            Community Feed
          </h1>
          <div className="flex items-center space-x-4">
            <span className="text-sm text-gray-500">
              Playto Engineering Challenge
            </span>
          </div>
        </div>
      </div>
    </nav>
  );
}

export default Navbar;
