(function () {
  'use strict';

  var reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  /* Hero slider: automatic cross-fade, with dots and a pause button. */
  function initSlider() {
    var hero = document.querySelector('.hero');
    if (!hero) return;
    var slides = hero.querySelectorAll('.hero-slide');
    if (slides.length < 2) return;
    var dots = hero.querySelectorAll('.hero-dot');
    var pauseBtn = hero.querySelector('.hero-pause');
    var captionNum = hero.querySelector('.hero-caption b');
    var captionText = hero.querySelector('.hero-caption span');
    var delay = 6000;
    var current = 0;
    var timer = null;
    var paused = reducedMotion;

    hero.style.setProperty('--slide-ms', delay + 'ms');

    function show(index) {
      slides[current].classList.remove('is-active');
      dots[current].classList.remove('is-active');
      dots[current].removeAttribute('aria-current');
      current = (index + slides.length) % slides.length;
      slides[current].classList.add('is-active');
      dots[current].classList.add('is-active');
      dots[current].setAttribute('aria-current', 'true');
      captionNum.textContent = '0' + (current + 1);
      captionText.textContent = slides[current].dataset.caption;
    }

    function stop() {
      clearTimeout(timer);
      timer = null;
    }

    function schedule() {
      stop();
      if (paused || document.hidden) return;
      timer = setTimeout(function () {
        show(current + 1);
        schedule();
      }, delay);
    }

    function setPaused(value) {
      paused = value;
      hero.classList.toggle('is-paused', paused);
      pauseBtn.setAttribute('aria-label', paused ? 'Play slideshow' : 'Pause slideshow');
      schedule();
    }

    dots.forEach(function (dot, i) {
      dot.addEventListener('click', function () {
        show(i);
        schedule();
      });
    });
    pauseBtn.addEventListener('click', function () {
      setPaused(!paused);
    });
    document.addEventListener('visibilitychange', schedule);

    show(0);
    setPaused(paused);
  }

  /* Menu: contact dropdown, current-section highlight, header shadow. */
  function initNav() {
    var nav = document.querySelector('.site-nav');

    /* Contact dropdown: opens on click (and on hover with a mouse, via CSS). */
    var drop = nav.querySelector('.nav-contact');
    if (drop) {
      var dropBtn = drop.querySelector('.nav-drop-toggle');
      var setDrop = function (open) {
        drop.classList.toggle('is-open', open);
        dropBtn.setAttribute('aria-expanded', String(open));
      };
      dropBtn.addEventListener('click', function () {
        setDrop(!drop.classList.contains('is-open'));
      });
      document.addEventListener('click', function (e) {
        if (!drop.contains(e.target)) setDrop(false);
      });
      document.addEventListener('keydown', function (e) {
        if (e.key === 'Escape' && drop.classList.contains('is-open')) {
          setDrop(false);
          dropBtn.focus();
        }
      });
    }

    /* Highlight the section currently on screen. */
    var links = nav.querySelectorAll('a[href^="#"]:not(.btn)');
    var spy = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (!entry.isIntersecting) return;
        links.forEach(function (link) {
          if (link.getAttribute('href') === '#' + entry.target.id) link.setAttribute('aria-current', 'true');
          else link.removeAttribute('aria-current');
        });
      });
    }, { rootMargin: '-45% 0px -50% 0px' });
    links.forEach(function (link) {
      var section = document.querySelector(link.getAttribute('href'));
      if (section) spy.observe(section);
    });

    var header = document.querySelector('.site-header');
    function onScroll() {
      header.classList.toggle('is-stuck', window.scrollY > 40);
    }
    window.addEventListener('scroll', onScroll, { passive: true });
    onScroll();
  }

  /* Fade sections in as they scroll into view. */
  function initReveal() {
    var items = document.querySelectorAll('.reveal');
    if (reducedMotion) {
      items.forEach(function (el) { el.classList.add('is-visible'); });
      return;
    }
    var observer = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) {
          entry.target.classList.add('is-visible');
          observer.unobserve(entry.target);
        }
      });
    }, { rootMargin: '0px 0px -8% 0px' });
    items.forEach(function (el) { observer.observe(el); });
  }

  /* Sends the enquiry to the server without leaving the page. Without JS the
     form still posts normally and the server redirects back with a message. */
  function initForm() {
    var form = document.querySelector('.contact-form');
    var note = form.querySelector('.form-note');
    var button = form.querySelector('button[type="submit"]');
    var serviceSelect = form.querySelector('#service');

    document.querySelectorAll('[data-service]').forEach(function (link) {
      link.addEventListener('click', function () {
        serviceSelect.value = link.dataset.service;
      });
    });

    function setNote(text, state) {
      note.textContent = text;
      note.classList.toggle('is-sent', state === 'sent');
      note.classList.toggle('is-error', state === 'error');
    }

    form.addEventListener('submit', function (e) {
      e.preventDefault();
      form.querySelectorAll('[aria-invalid]').forEach(function (el) { el.removeAttribute('aria-invalid'); });
      if (!form.checkValidity()) {
        var invalid = form.querySelector(':invalid');
        invalid.setAttribute('aria-invalid', 'true');
        invalid.focus();
        setNote('Please fill in your name, phone and what you need.', 'error');
        return;
      }
      button.disabled = true;
      setNote('Sending...', '');
      fetch(form.action, {
        method: 'POST',
        headers: { 'Accept': 'application/json' },
        body: new FormData(form)
      })
        .then(function (res) { return res.json(); })
        .then(function (data) {
          if (data.ok) {
            form.reset();
            setNote(data.message || 'Thank you. We will contact you shortly.', 'sent');
            return;
          }
          Object.keys(data.errors || {}).forEach(function (name) {
            var field = form.elements[name];
            if (field) field.setAttribute('aria-invalid', 'true');
          });
          var first = form.querySelector('[aria-invalid]');
          if (first) first.focus();
          setNote(data.message || 'Something went wrong. Please try again.', 'error');
        })
        .catch(function () {
          setNote('We could not send your request. Please check your connection or call us directly.', 'error');
        })
        .then(function () { button.disabled = false; });
    });
  }

  /* Service division tabs. Each division has its own address (#environmental, #real-estate)
     so links from the strip, the service pages and shared links open the right one.
     Without JS every division simply shows in turn. */
  function initTabs() {
    var tabs = document.querySelectorAll('.svc-tab');
    if (!tabs.length) return;

    function panelOf(tab) { return document.getElementById(tab.getAttribute('aria-controls')); }

    function select(tab) {
      tabs.forEach(function (t) {
        var on = t === tab;
        t.setAttribute('aria-selected', String(on));
        t.tabIndex = on ? 0 : -1;
        panelOf(t).hidden = !on;
      });
    }

    function tabForHash(hash) {
      var found = null;
      tabs.forEach(function (t) { if ('#' + panelOf(t).dataset.hash === hash) found = t; });
      return found;
    }

    function openFromHash(scroll) {
      var tab = tabForHash(location.hash);
      if (!tab) return false;
      select(tab);
      if (scroll) panelOf(tab).querySelector('.svc-panel-head').scrollIntoView({ block: 'start' });
      return true;
    }

    tabs.forEach(function (tab, i) {
      tab.addEventListener('click', function () {
        select(tab);
        history.replaceState(null, '', '#' + panelOf(tab).dataset.hash);
      });
      tab.addEventListener('keydown', function (e) {
        var step = e.key === 'ArrowRight' ? 1 : e.key === 'ArrowLeft' ? -1 : 0;
        if (!step) return;
        var next = tabs[(i + step + tabs.length) % tabs.length];
        select(next);
        next.focus();
      });
    });
    // The strip's division links: open the tab first so the browser scrolls to a visible heading.
    document.querySelectorAll('[data-tab-link]').forEach(function (link) {
      link.addEventListener('click', function () {
        select(document.getElementById('tab-' + link.dataset.tabLink));
      });
    });
    window.addEventListener('hashchange', function () { openFromHash(true); });
    if (!openFromHash(true)) select(tabs[0]);
  }

  /* Showcase video. Browsers only allow sound after the visitor taps, so it starts
     silently with a "Tap for sound" button. It pauses when scrolled out of view.
     It doesn't start by itself for visitors who prefer reduced motion or use data saver. */
  function initVideo() {
    var video = document.querySelector('.showcase-video');
    if (!video) return;
    var soundBtn = document.querySelector('.sound-btn');
    var saveData = navigator.connection && navigator.connection.saveData;
    var autoplay = !reducedMotion && !saveData && 'IntersectionObserver' in window;
    var userPaused = false;
    var withSound = false;

    function showButton(show) { if (soundBtn) soundBtn.hidden = !show; }

    if (soundBtn) {
      showButton(true);
      soundBtn.addEventListener('click', function () {
        withSound = true;
        video.loop = false;
        video.muted = false;
        video.currentTime = 0;
        video.play().catch(function () {});
        showButton(false);
      });
    }
    video.addEventListener('volumechange', function () {
      if (!video.muted && video.volume > 0) { withSound = true; showButton(false); }
    });
    video.addEventListener('ended', function () {
      // After playing through with sound, carry on silently and offer sound again.
      withSound = false;
      video.muted = true;
      video.loop = true;
      showButton(true);
      if (autoplay) video.play().catch(function () {});
    });
    video.addEventListener('pause', function () { if (!video.dataset.autoPausing) userPaused = true; });
    video.addEventListener('play', function () { userPaused = false; });

    if (!autoplay) return;
    video.preload = 'auto';  // start downloading now so it begins playing sooner
    new IntersectionObserver(function (entries) {
      var entry = entries[0];
      if (entry.isIntersecting && !userPaused) {
        if (!withSound) { video.muted = true; video.loop = true; }
        video.play().catch(function () {});
      } else if (!entry.isIntersecting && !video.paused) {
        video.dataset.autoPausing = '1';
        video.pause();
        delete video.dataset.autoPausing;
      }
    }, { threshold: 0.5 }).observe(video);
  }

  initTabs();
  initVideo();
  initSlider();
  initNav();
  initReveal();
  initForm();
})();
