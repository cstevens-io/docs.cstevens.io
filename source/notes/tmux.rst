tmux QOL settings
=================

a.k.a. tmux config for screen users

~/.tmux.conf
------------

.. code-block:: text

    # tmux config for screen users

    # remap prefix from 'C-b' to 'C-a'
    unbind C-b
    set-option -g prefix C-a
    bind-key C-a send-prefix

    # split panes using | and -
    bind | split-window -h
    bind - split-window -v
    unbind '"'
    unbind %

    # switch panes using Alt-arrow without prefix
    bind -n M-Left select-pane -L
    bind -n M-Right select-pane -R
    bind -n M-Up select-pane -U
    bind -n M-Down select-pane -D

    # enable mouse mode (tmux 2.1 and above)
    # this allows scrolling in panes with the mousewheel,
    # select active pane with mouse, adjust pane size with mouse
    set -g mouse on

    # bring cursor to beginning of line like in screen: C-a, a
    bind a send-prefix

    # bind '"' to choose-window, instead of 'w', similar to screen
    unbind w
    bind '"' choose-window

    # bind 'A' to rename-window, similar to screen
    bind A command-prompt -I "#W" "rename-window '%%'"

    # bind C-a, C-a to previous window
    bind C-a last-window

    # bind 'k' to kill-window (instead of &)
    unbind &
    bind k confirm-before -p "kill window #W? (y/n)" kill-window

    # bind 's' to synchronize typing in panes
    # rebind 's' choose-tree to 'S'
    bind S choose-tree
    bind s set-window-option synchronize-panes

    # rename window to reflect current program
    # will not rename windows that have been manually named
    setw -g automatic-rename on

    # don't renumber windows when a window is closed
    set -g renumber-windows off
